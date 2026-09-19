from django.conf import settings
from django.db import models


class UsuarioPerfil(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    documento = models.CharField(max_length=27, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    empresa = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = 'usuario_perfiles'

    def __str__(self):
        return f'Perfil de {self.usuario.username}'
