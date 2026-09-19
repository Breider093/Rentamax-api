from decimal import Decimal

from django.db import models
from django.utils import timezone


class Remision(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        RESERVADA = 'RESERVADA', 'Reservada'
        ENTREGADA = 'ENTREGADA', 'Entregada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    class Prioridad(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        URGENTE = 'URGENTE', 'Urgente'

    numero = models.CharField(max_length=30, unique=True, blank=True)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='remisiones',
    )
    transportador = models.ForeignKey(
        'transportadores.Transportador',
        on_delete=models.PROTECT,
        related_name='remisiones',
        null=True,
        blank=True,
    )
    fecha_emision = models.DateField(default=timezone.localdate)
    fecha_entrega_programada = models.DateField()
    fecha_entrega_real = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    prioridad = models.CharField(
        max_length=15,
        choices=Prioridad.choices,
        default=Prioridad.NORMAL,
    )
    observaciones = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'remisiones'
        ordering = ['-fecha_emision', '-id']
        indexes = [
            models.Index(fields=['cliente'], name='remisiones_cliente_idx'),
            models.Index(fields=['estado', 'fecha_entrega_programada'], name='remisiones_estado_fecha_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = timezone.now().strftime('REM-%Y%m%d-%H%M%S-%f')
        super().save(*args, **kwargs)

    def recalcular_totales(self):
        subtotal = self.detalles.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
        self.subtotal = subtotal
        self.total = subtotal + self.impuestos
        self.save(update_fields=['subtotal', 'total', 'actualizado_en'])

    def __str__(self):
        return self.numero


class RemisionDetalle(models.Model):
    remision = models.ForeignKey(
        Remision,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        related_name='detalles_remision',
    )
    descripcion = models.CharField(max_length=255)
    unidad_medida = models.CharField(max_length=30, blank=True)
    cantidad = models.DecimalField(max_digits=14, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'remision_detalles'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['remision', 'producto'], name='remision_producto_unico'),
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='remision_cantidad_positiva'),
            models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='remision_precio_no_negativo'),
        ]
        indexes = [
            models.Index(fields=['producto'], name='remision_detalle_producto_idx'),
        ]

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal('0.01'))
        if not self.descripcion:
            self.descripcion = self.producto.descripcion
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.remision.numero} - {self.descripcion}'


class RemisionReserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    remision = models.ForeignKey(Remision, on_delete=models.CASCADE, related_name='reservas')
    fecha_reserva = models.DateField(default=timezone.localdate)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    observaciones = models.TextField(blank=True)
    confirmada_at = models.DateTimeField(null=True, blank=True)
    cancelada_at = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'remision_reservas'
        ordering = ['-fecha_reserva', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['remision'],
                condition=models.Q(estado__in=['PENDIENTE', 'CONFIRMADA']),
                name='remision_reserva_activa_unica',
            ),
        ]


class RemisionAlarma(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        RESUELTA = 'RESUELTA', 'Resuelta'
        CANCELADA = 'CANCELADA', 'Cancelada'

    remision = models.ForeignKey(Remision, on_delete=models.CASCADE, related_name='alarmas')
    tipo = models.CharField(max_length=30)
    prioridad = models.CharField(max_length=15, default=Remision.Prioridad.NORMAL, choices=Remision.Prioridad.choices)
    descripcion = models.TextField()
    fecha_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    resuelta_at = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'remision_alarmas'
        ordering = ['estado', 'fecha_limite', '-id']
        indexes = [models.Index(fields=['estado', 'fecha_limite'], name='alarmas_estado_fecha_idx')]
