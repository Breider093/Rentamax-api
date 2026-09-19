from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Factura(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EMITIDA = 'EMITIDA', 'Emitida'
        PAGADA = 'PAGADA', 'Pagada'
        VENCIDA = 'VENCIDA', 'Vencida'
        ANULADA = 'ANULADA', 'Anulada'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TARJETA = 'TARJETA', 'Tarjeta'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'

    numero = models.CharField(max_length=30, unique=True)
    cliente = models.ForeignKey(
        'clientes.Cliente', on_delete=models.PROTECT, related_name='facturas', null=True
    )
    remision = models.OneToOneField(
        'remisiones.Remision',
        on_delete=models.PROTECT,
        related_name='factura',
        null=True,
        blank=True,
    )
    cotizacion = models.OneToOneField(
        'cotizaciones.Cotizacion',
        on_delete=models.PROTECT,
        related_name='factura',
        null=True,
        blank=True,
    )
    fecha_emision = models.DateField(default=timezone.localdate)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='facturas_creadas',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facturas'
        ordering = ['-creado_en', '-id']
        indexes = [
            models.Index(fields=['cliente'], name='factura_cliente_idx'),
            models.Index(fields=['fecha_emision'], name='factura_fecha_idx'),
            models.Index(fields=['estado'], name='factura_estado_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['remision'], condition=models.Q(remision__isnull=False),
                name='factura_remision_unica',
            ),
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name='factura_subtotal_no_negativo'),
            models.CheckConstraint(condition=models.Q(impuestos__gte=0), name='factura_impuestos_no_negativos'),
            models.CheckConstraint(condition=models.Q(total__gte=0), name='factura_total_no_negativo'),
        ]

    def __str__(self):
        return self.numero

    def recalcular_totales(self):
        self.subtotal = self.detalles.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
        self.total = self.subtotal + self.impuestos
        self.save(update_fields=['subtotal', 'total', 'actualizado_en'])

    @property
    def saldo_pendiente(self):
        pagado = self.pagos.aggregate(total=models.Sum('monto'))['total'] or Decimal('0.00')
        return max(self.total - pagado, Decimal('0.00'))


class FacturaDetalle(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(
        'productos.Producto', on_delete=models.PROTECT, related_name='detalles_factura'
    )
    descripcion = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=14, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'factura_detalles'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['factura', 'producto'], name='factura_producto_unico'),
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='factura_cantidad_positiva'),
            models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='factura_precio_no_negativo'),
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name='factura_detalle_subtotal_no_negativo'),
        ]
        indexes = [models.Index(fields=['factura'], name='factura_detalle_factura_idx')]

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
        if not self.descripcion:
            self.descripcion = self.producto.descripcion
        super().save(*args, **kwargs)


class FacturaPago(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='pagos')
    metodo_pago = models.CharField(max_length=20, choices=Factura.MetodoPago.choices)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'factura_pagos'
        ordering = ['-fecha_pago', '-id']
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name='factura_pago_monto_positivo'),
        ]
