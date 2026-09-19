from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Devolucion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PROCESADA = 'PROCESADA', 'Procesada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    class EstadoFactura(models.TextChoices):
        SIN_FACTURA = 'SIN_FACTURA', 'Sin factura'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        GENERADA = 'GENERADA', 'Generada'
        VENCIDA = 'VENCIDA', 'Vencida'

    numero = models.CharField(max_length=30, unique=True, blank=True)
    cliente = models.ForeignKey(
        'clientes.Cliente', on_delete=models.PROTECT, related_name='devoluciones'
    )
    obra = models.ForeignKey(
        'obras.Obra', on_delete=models.PROTECT, related_name='devoluciones'
    )
    transportador = models.ForeignKey(
        'transportadores.Transportador', on_delete=models.PROTECT, related_name='devoluciones'
    )
    factura = models.ForeignKey(
        'facturas.Factura', on_delete=models.PROTECT, null=True, blank=True,
        related_name='devoluciones',
    )
    fecha_factura = models.DateField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    precio_transporte = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    estado_factura = models.CharField(
        max_length=20, choices=EstadoFactura.choices, default=EstadoFactura.SIN_FACTURA
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='devoluciones_creadas',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devoluciones'
        ordering = ['-creado_en', '-id']
        indexes = [
            models.Index(fields=['cliente'], name='devolucion_cliente_idx'),
            models.Index(fields=['estado'], name='devolucion_estado_idx'),
            models.Index(fields=['estado_factura'], name='devolucion_factura_estado_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio_transporte__gte=0),
                name='devolucion_transporte_no_negativo',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = timezone.now().strftime('DEV-%Y%m%d-%H%M%S-%f')
        if self.factura_id and self.estado_factura == self.EstadoFactura.SIN_FACTURA:
            self.estado_factura = self.EstadoFactura.PENDIENTE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero


class DevolucionDetalle(models.Model):
    class Motivo(models.TextChoices):
        DEFECTUOSO = 'DEFECTUOSO', 'Defectuoso'
        EXCESO_PEDIDO = 'EXCESO_PEDIDO', 'Exceso de pedido'
        CAMBIO_PRODUCTO = 'CAMBIO_PRODUCTO', 'Cambio de producto'
        OTRO = 'OTRO', 'Otro'

    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(
        'productos.Producto', on_delete=models.PROTECT, related_name='detalles_devolucion'
    )
    cantidad = models.DecimalField(max_digits=14, decimal_places=3)
    peso_unitario = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    total_kg = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    motivo = models.CharField(max_length=30, choices=Motivo.choices)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'devolucion_detalles'
        ordering = ['id']
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='devolucion_cantidad_positiva'),
            models.CheckConstraint(condition=models.Q(peso_unitario__gte=0), name='devolucion_peso_no_negativo'),
            models.CheckConstraint(condition=models.Q(total_kg__gte=0), name='devolucion_total_kg_no_negativo'),
        ]
        indexes = [
            models.Index(fields=['devolucion'], name='devolucion_detalle_dev_idx'),
            models.Index(fields=['producto'], name='devolucion_detalle_prod_idx'),
        ]

    def save(self, *args, **kwargs):
        self.total_kg = (self.cantidad * self.peso_unitario).quantize(Decimal('0.001'))
        super().save(*args, **kwargs)
