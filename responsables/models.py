from django.db import models


class Responsable(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    documento = models.CharField(max_length=27, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    direccion = models.CharField(max_length=150, blank=True)
    celular = models.CharField(max_length=20, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'responsables'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['estado'], name='responsable_estado_idx'),
            models.Index(fields=['apellido', 'nombre'], name='responsable_nombre_idx'),
        ]

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.documento})'
