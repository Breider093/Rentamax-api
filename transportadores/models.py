from django.db import models
from django.utils import timezone


class Transportador(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    codigo = models.CharField(max_length=20, unique=True, blank=True)
    nombre = models.CharField(max_length=150)
    documento = models.CharField(max_length=30, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=150, blank=True)
    licencia_numero = models.CharField(max_length=50, unique=True, null=True, blank=True)
    licencia_categoria = models.CharField(max_length=20, blank=True)
    licencia_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transportadores'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['estado'], name='transportador_estado_idx'),
            models.Index(fields=['nombre'], name='transportador_nombre_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Transportador.objects.order_by('-id').first()
            siguiente = (ultimo.id + 1) if ultimo else 1
            self.codigo = f'TR{siguiente:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Vehiculo(models.Model):
    class Tipo(models.TextChoices):
        CAMION = 'CAMION', 'Camión'
        FURGON = 'FURGON', 'Furgón'
        CAMIONETA = 'CAMIONETA', 'Camioneta'

    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'
        MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'

    placa = models.CharField(max_length=15, unique=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    marca = models.CharField(max_length=80, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    capacidad_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehiculos'
        ordering = ['placa']

    def __str__(self):
        return f'{self.placa} - {self.get_tipo_display()}'


class TransportadorVehiculo(models.Model):
    transportador = models.ForeignKey(Transportador, on_delete=models.CASCADE, related_name='asignaciones_vehiculo')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='asignaciones_transportador')
    es_principal = models.BooleanField(default=False)
    fecha_asignacion = models.DateField(default=timezone.localdate)
    fecha_desasignacion = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'transportador_vehiculos'
        constraints = [
            models.UniqueConstraint(fields=['transportador', 'vehiculo'], name='transportador_vehiculo_unico'),
        ]


class Viaje(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADO = 'PROGRAMADO', 'Programado'
        EN_CURSO = 'EN_CURSO', 'En curso'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    codigo = models.CharField(max_length=30, unique=True, blank=True)
    transportador = models.ForeignKey(Transportador, on_delete=models.PROTECT, related_name='viajes')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name='viajes', null=True, blank=True)
    origen = models.CharField(max_length=150, blank=True)
    destino = models.CharField(max_length=150)
    pais_destino = models.CharField(max_length=100, default='Colombia')
    fecha_salida = models.DateTimeField()
    fecha_llegada_estimada = models.DateTimeField(null=True, blank=True)
    fecha_llegada_real = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADO)
    observaciones = models.TextField(blank=True)
    remisiones = models.ManyToManyField(
        'remisiones.Remision',
        through='ViajeRemision',
        related_name='viajes',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'viajes'
        ordering = ['-fecha_salida', '-id']
        indexes = [
            models.Index(fields=['transportador'], name='viaje_transportador_idx'),
            models.Index(fields=['estado', 'fecha_salida'], name='viaje_estado_fecha_idx'),
            models.Index(fields=['destino'], name='viaje_destino_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = timezone.now().strftime('VIA-%Y%m%d-%H%M%S-%f')
        super().save(*args, **kwargs)


class ViajeRemision(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        CARGADA = 'CARGADA', 'Cargada'
        ENTREGADA = 'ENTREGADA', 'Entregada'
        DEVUELTA = 'DEVUELTA', 'Devuelta'

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='remisiones_asignadas')
    remision = models.ForeignKey('remisiones.Remision', on_delete=models.CASCADE, related_name='asignaciones_viaje')
    orden_entrega = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'viaje_remisiones'
        constraints = [
            models.UniqueConstraint(fields=['viaje', 'remision'], name='viaje_remision_unico'),
            models.UniqueConstraint(fields=['remision'], name='remision_unica_en_viaje'),
        ]
        indexes = [
            models.Index(fields=['remision'], name='viaje_remision_remision_idx'),
        ]
