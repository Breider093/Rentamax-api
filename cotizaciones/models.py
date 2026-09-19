from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Cotizacion(models.Model):
	class Estado(models.TextChoices):
		PENDIENTE = 'PENDIENTE', 'Pendiente'
		APROBADA = 'APROBADA', 'Aprobada'
		RECHAZADA = 'RECHAZADA', 'Rechazada'
		VENCIDA = 'VENCIDA', 'Vencida'
		CANCELADA = 'CANCELADA', 'Cancelada'
		CONVERTIDA = 'CONVERTIDA', 'Convertida'

	numero = models.CharField(max_length=30, unique=True, blank=True)
	cliente = models.ForeignKey(
		'clientes.Cliente', on_delete=models.PROTECT, related_name='cotizaciones'
	)
	fecha_emision = models.DateField(default=timezone.localdate)
	vigencia_dias = models.PositiveIntegerField(default=30)
	fecha_vencimiento = models.DateField(null=True, blank=True)
	estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
	observaciones = models.TextField(blank=True)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	creado_por = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='cotizaciones_creadas',
	)
	creado_en = models.DateTimeField(auto_now_add=True)
	actualizado_en = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'cotizaciones'
		ordering = ['-fecha_emision', '-id']
		indexes = [
			models.Index(fields=['cliente'], name='cotizacion_cliente_idx'),
			models.Index(fields=['fecha_emision'], name='cotizacion_fecha_idx'),
			models.Index(fields=['estado'], name='cotizacion_estado_idx'),
		]
		constraints = [
			models.CheckConstraint(
				condition=(
					models.Q(fecha_vencimiento__isnull=True)
					| models.Q(fecha_vencimiento__gte=models.F('fecha_emision'))
				),
				name='cotizacion_fecha_valida',
			),
			models.CheckConstraint(
				condition=models.Q(vigencia_dias__gt=0),
				name='cotizacion_vigencia_positiva',
			),
		]

	def save(self, *args, **kwargs):
		if not self.numero:
			self.numero = timezone.now().strftime('COT-%Y%m%d-%H%M%S-%f')
		if not self.fecha_vencimiento:
			self.fecha_vencimiento = self.fecha_emision + timedelta(days=self.vigencia_dias)
		super().save(*args, **kwargs)

	def recalcular_totales(self):
		totales = self.detalles.aggregate(
			subtotal=models.Sum('subtotal'),
			iva=models.Sum('iva_linea'),
		)
		self.subtotal = totales['subtotal'] or Decimal('0.00')
		if totales['iva']:
			self.impuestos = totales['iva']
		self.total = self.subtotal + self.impuestos
		self.save(update_fields=['subtotal', 'impuestos', 'total', 'actualizado_en'])

	def __str__(self):
		return self.numero


class CotizacionDetalle(models.Model):
	cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
	producto = models.ForeignKey(
		'productos.Producto', on_delete=models.PROTECT, related_name='detalles_cotizacion'
	)
	descripcion = models.CharField(max_length=255)
	cantidad = models.DecimalField(max_digits=14, decimal_places=3)
	precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	iva_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)

	class Meta:
		db_table = 'cotizacion_detalles'
		ordering = ['id']
		constraints = [
			models.UniqueConstraint(fields=['cotizacion', 'producto'], name='cotizacion_producto_unico'),
			models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='cotizacion_cantidad_positiva'),
			models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='cotizacion_precio_no_negativo'),
			models.CheckConstraint(condition=models.Q(subtotal__gte=0), name='cotizacion_subtotal_no_negativo'),
			models.CheckConstraint(condition=models.Q(iva_linea__gte=0), name='cotizacion_iva_no_negativo'),
			models.CheckConstraint(condition=models.Q(total_linea__gte=0), name='cotizacion_total_linea_no_negativo'),
		]
		indexes = [
			models.Index(fields=['cotizacion'], name='cotizacion_detalle_cot_idx'),
		]

	def save(self, *args, **kwargs):
		self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
		self.total_linea = self.subtotal + self.iva_linea
		if not self.descripcion:
			self.descripcion = self.producto.descripcion
		super().save(*args, **kwargs)

