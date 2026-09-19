from decimal import Decimal

from django.db import models

from clientes.models import Cliente
from obras.models import Obra
from productos.models import Producto


class Prestamo(models.Model):
    class Estado(models.TextChoices):
        RESERVADO = 'RESERVADO', 'Reservado'
        ACTIVO = 'ACTIVO', 'Activo'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        FINALIZADO = 'FINALIZADO', 'Finalizado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='prestamos',
    )
    obra = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        related_name='prestamos',
        null=True,
        blank=True,
    )
    fecha_reserva = models.DateField()
    fecha_entrega = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.RESERVADO,
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacion = models.CharField(max_length=400, blank=True)

    class Meta:
        db_table = 'prestamos'
        ordering = ['-fecha_reserva', '-id']
        indexes = [
            models.Index(fields=['cliente', 'estado'], name='prestamos_cliente_estado_idx'),
            models.Index(fields=['estado'], name='prestamos_estado_idx'),
        ]

    def __str__(self):
        return f'Préstamo {self.pk} - {self.cliente}'

    def actualizar_total(self):
        self.total = self.detalles.aggregate(
            total=models.Sum('subtotal')
        )['total'] or Decimal('0.00')
        self.save(update_fields=['total'])


class PrestamoDetalle(models.Model):
    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_prestamo',
        null=True,
        blank=True,
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'prestamo_detalles'
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(
            Decimal('0.01')
        )
        super().save(*args, **kwargs)
        self.prestamo.actualizar_total()

    def delete(self, *args, **kwargs):
        prestamo = self.prestamo
        result = super().delete(*args, **kwargs)
        prestamo.actualizar_total()
        return result


class EquipoObra(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        EN_USO = 'EN_USO', 'En uso'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='equipos_obra',
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name='equipos_obra',
    )
    obra = models.ForeignKey(
        Obra, on_delete=models.PROTECT, related_name='equipos_obra',
    )
    descripcion = models.CharField(max_length=255, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVO,
    )

    class Meta:
        db_table = 'equipo_obra'
        ordering = ['obra__nombre', 'producto__descripcion', 'id']
        indexes = [
            models.Index(fields=['cliente', 'obra'], name='equipo_obra_cliente_obra_idx'),
            models.Index(fields=['estado'], name='equipo_obra_estado_idx'),
        ]
