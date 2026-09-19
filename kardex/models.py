from decimal import Decimal

from django.db import models
from django.utils import timezone

from clientes.models import Cliente
from obras.models import Obra
from productos.models import Producto


class KardexMovimiento(models.Model):
    class Tipo(models.TextChoices):
        VENTA = 'VENTA', 'Venta'
        PRESTAMO = 'PRESTAMO', 'Préstamo'
        DEVOLUCION = 'DEVOLUCION', 'Devolución'
        PAGO = 'PAGO', 'Pago'
        REPOSICION = 'REPOSICION', 'Reposición'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='movimientos_kardex',
    )
    obra = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        related_name='movimientos_kardex',
        null=True,
        blank=True,
    )
    remision = models.ForeignKey(
        'remisiones.Remision',
        on_delete=models.SET_NULL,
        related_name='movimientos_kardex',
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    numero_documento = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    descripcion = models.CharField(max_length=255, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=30, default='ACTIVO')

    class Meta:
        db_table = 'kardex_movimientos'
        ordering = ['fecha', 'id']
        indexes = [
            models.Index(fields=['cliente', 'fecha'], name='kardex_cliente_fecha_idx'),
            models.Index(fields=['tipo'], name='kardex_tipo_idx'),
            models.Index(fields=['obra'], name='kardex_obra_idx'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.cliente}'


class KardexDetalle(models.Model):
    movimiento = models.ForeignKey(
        KardexMovimiento,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_kardex',
        null=True,
        blank=True,
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'kardex_detalles'
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(
            Decimal('0.01')
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Detalle {self.pk} de movimiento {self.movimiento_id}'
