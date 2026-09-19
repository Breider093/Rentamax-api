from django.db import models

from clientes.models import Cliente


class Obra(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = 'ACTIVA', 'Activa'
        INACTIVA = 'INACTIVA', 'Inactiva'
        FINALIZADA = 'FINALIZADA', 'Finalizada'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='obras',
    )
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'obras'
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['cliente'], name='obras_cliente_idx'),
        ]

    def __str__(self):
        return f'{self.nombre} - {self.cliente.razon_social}'
