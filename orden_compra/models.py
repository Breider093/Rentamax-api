from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class OrdenCompra(models.Model):
	class Estado(models.TextChoices):
		PENDIENTE = 'PENDIENTE', 'Pendiente'
		APROBADA = 'APROBADA', 'Aprobada'
		COMPLETADA = 'COMPLETADA', 'Completada'
		CANCELADA = 'CANCELADA', 'Cancelada'

	numero = models.CharField(max_length=30, unique=True, blank=True)
	proveedor = models.ForeignKey(
		'productos.Proveedor', on_delete=models.PROTECT, related_name='ordenes_compra'
	)
	fecha_emision = models.DateField(default=timezone.localdate)
	fecha_entrega_programada = models.DateField()
	estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
	observaciones = models.TextField(blank=True)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	creado_por = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
		related_name='ordenes_compra_creadas',
	)
	creado_en = models.DateTimeField(auto_now_add=True)
	actualizado_en = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'ordenes_compra'
		ordering = ['-fecha_emision', '-id']
		indexes = [
			models.Index(fields=['proveedor'], name='orden_compra_proveedor_idx'),
			models.Index(fields=['estado', 'fecha_entrega_programada'], name='orden_compra_estado_fecha_idx'),
		]

	def save(self, *args, **kwargs):
		if not self.numero:
			self.numero = timezone.now().strftime('OC-%Y%m%d-%H%M%S-%f')
		super().save(*args, **kwargs)

	def recalcular_totales(self):
		subtotal = self.detalles.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
		self.subtotal = subtotal
		self.total = subtotal + self.impuestos
		self.save(update_fields=['subtotal', 'total', 'actualizado_en'])

	def __str__(self):
		return self.numero


class OrdenCompraDetalle(models.Model):
	orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
	producto = models.ForeignKey(
		'productos.Producto', on_delete=models.PROTECT, related_name='detalles_orden_compra'
	)
	descripcion = models.CharField(max_length=255, blank=True)
	cantidad = models.DecimalField(max_digits=14, decimal_places=3)
	precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	cantidad_recibida = models.DecimalField(max_digits=14, decimal_places=3, default=0)

	class Meta:
		db_table = 'orden_compra_detalles'
		ordering = ['id']
		constraints = [
			models.UniqueConstraint(fields=['orden_compra', 'producto'], name='orden_compra_producto_unico'),
			models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='orden_compra_cantidad_positiva'),
			models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='orden_compra_precio_no_negativo'),
			models.CheckConstraint(condition=models.Q(cantidad_recibida__gte=0), name='orden_compra_recibida_no_negativa'),
		]

	def save(self, *args, **kwargs):
		self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
		if not self.descripcion:
			self.descripcion = self.producto.descripcion
		super().save(*args, **kwargs)


class Entrada(models.Model):
	class Estado(models.TextChoices):
		PENDIENTE = 'PENDIENTE', 'Pendiente'
		CONFIRMADA = 'CONFIRMADA', 'Confirmada'
		CANCELADA = 'CANCELADA', 'Cancelada'

	numero = models.CharField(max_length=30, unique=True, blank=True)
	proveedor = models.ForeignKey(
		'productos.Proveedor', on_delete=models.PROTECT, related_name='entradas'
	)
	orden_compra = models.ForeignKey(
		OrdenCompra, on_delete=models.PROTECT, null=True, blank=True, related_name='entradas'
	)
	fecha_entrada = models.DateField(default=timezone.localdate)
	numero_factura = models.CharField(max_length=100, blank=True)
	estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
	observaciones = models.TextField(blank=True)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	creado_en = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'entradas'
		ordering = ['-fecha_entrada', '-id']

	def save(self, *args, **kwargs):
		if not self.numero:
			self.numero = timezone.now().strftime('ENT-%Y%m%d-%H%M%S-%f')
		super().save(*args, **kwargs)

	def recalcular_totales(self):
		self.subtotal = self.detalles.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
		self.total = self.subtotal
		self.save(update_fields=['subtotal', 'total'])


class EntradaDetalle(models.Model):
	entrada = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name='detalles')
	producto = models.ForeignKey(
		'productos.Producto', on_delete=models.PROTECT, related_name='detalles_entrada'
	)
	cantidad = models.DecimalField(max_digits=14, decimal_places=3)
	precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
	lote = models.CharField(max_length=100, blank=True)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

	class Meta:
		db_table = 'entrada_detalles'
		ordering = ['id']
		constraints = [
			models.UniqueConstraint(fields=['entrada', 'producto'], name='entrada_producto_unico'),
			models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='entrada_cantidad_positiva'),
			models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='entrada_precio_no_negativo'),
		]

	def save(self, *args, **kwargs):
		self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
		super().save(*args, **kwargs)


class Inventario(models.Model):
	producto = models.OneToOneField('productos.Producto', on_delete=models.CASCADE, related_name='inventario')
	proveedor = models.ForeignKey(
		'productos.Proveedor', on_delete=models.PROTECT, null=True, blank=True,
		related_name='inventarios',
	)
	codigo = models.CharField(max_length=50, blank=True)
	descripcion = models.CharField(max_length=255, blank=True)
	saldo_proveedor = models.IntegerField(default=0)
	remision = models.IntegerField(default=0)
	devolucion = models.IntegerField(default=0)
	reposicion = models.IntegerField(default=0)
	en_alquiler = models.IntegerField(default=0)
	en_bodega = models.IntegerField(default=0)
	estado = models.CharField(max_length=50, default='Disponible')
	existencia = models.DecimalField(max_digits=14, decimal_places=3, default=0)
	actualizado_en = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'inventario'


class Salida(models.Model):
	class Tipo(models.TextChoices):
		VENTA = 'VENTA', 'Venta'
		DEVOLUCION = 'DEVOLUCION', 'Devolución'
		TRASLADO = 'TRASLADO', 'Traslado'

	class Estado(models.TextChoices):
		PENDIENTE = 'PENDIENTE', 'Pendiente'
		COMPLETADA = 'COMPLETADA', 'Completada'
		CANCELADA = 'CANCELADA', 'Cancelada'

	numero = models.CharField(max_length=30, unique=True, blank=True)
	fecha = models.DateField(default=timezone.localdate)
	cliente = models.ForeignKey(
		'clientes.Cliente', on_delete=models.PROTECT, null=True, blank=True, related_name='salidas'
	)
	tipo = models.CharField(max_length=30, choices=Tipo.choices)
	responsable = models.ForeignKey(
		'responsables.Responsable', on_delete=models.SET_NULL, null=True, blank=True,
		related_name='salidas_responsable',
	)
	estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
	observaciones = models.TextField(blank=True)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	creado_en = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'salidas'
		ordering = ['-fecha', '-id']
		indexes = [
			models.Index(fields=['cliente'], name='salida_cliente_idx'),
			models.Index(fields=['estado', 'fecha'], name='salida_estado_fecha_idx'),
		]

	def save(self, *args, **kwargs):
		if not self.numero:
			self.numero = timezone.now().strftime('SAL-%Y%m%d-%H%M%S-%f')
		super().save(*args, **kwargs)

	def recalcular_totales(self):
		self.subtotal = self.detalles.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
		self.total = self.subtotal + self.impuestos
		self.save(update_fields=['subtotal', 'total'])


class SalidaDetalle(models.Model):
	salida = models.ForeignKey(Salida, on_delete=models.CASCADE, related_name='detalles')
	producto = models.ForeignKey(
		'productos.Producto', on_delete=models.PROTECT, related_name='detalles_salida'
	)
	cantidad = models.DecimalField(max_digits=14, decimal_places=3)
	precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	iva_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	total_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)

	class Meta:
		db_table = 'salida_detalles'
		ordering = ['id']
		constraints = [
			models.UniqueConstraint(fields=['salida', 'producto'], name='salida_producto_unico'),
			models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='salida_cantidad_positiva'),
			models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='salida_precio_no_negativo'),
		]

	def save(self, *args, **kwargs):
		self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
		self.total_linea = self.subtotal + self.iva_linea
		super().save(*args, **kwargs)


class MovimientoInventario(models.Model):
	class Tipo(models.TextChoices):
		ENTRADA = 'ENTRADA', 'Entrada'
		SALIDA = 'SALIDA', 'Salida'
		DEVOLUCION = 'DEVOLUCION', 'Devolución'
		AJUSTE = 'AJUSTE', 'Ajuste'

	producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='movimientos_inventario')
	tipo = models.CharField(max_length=20, choices=Tipo.choices)
	cantidad = models.DecimalField(max_digits=14, decimal_places=3)
	referencia_tipo = models.CharField(max_length=30, blank=True)
	referencia_id = models.PositiveBigIntegerField(null=True, blank=True)
	lote = models.CharField(max_length=100, blank=True)
	fecha = models.DateTimeField(default=timezone.now)
	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

	class Meta:
		db_table = 'movimientos_inventario'
		ordering = ['-fecha', '-id']
		indexes = [
			models.Index(fields=['producto', 'fecha'], name='mov_inv_producto_fecha_idx'),
			models.Index(fields=['referencia_tipo', 'referencia_id'], name='mov_inv_referencia_idx'),
		]


class Lote(models.Model):
	producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='lotes')
	codigo = models.CharField(max_length=100)
	fecha_vencimiento = models.DateField(null=True, blank=True)
	cantidad_disponible = models.DecimalField(max_digits=14, decimal_places=3, default=0)

	class Meta:
		db_table = 'lotes'
		constraints = [
			models.UniqueConstraint(fields=['producto', 'codigo'], name='lote_producto_codigo_unico'),
			models.CheckConstraint(condition=models.Q(cantidad_disponible__gte=0), name='lote_cantidad_no_negativa'),
		]

