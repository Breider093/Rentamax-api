# empresas/models.py
from django.conf import settings
from django.db import models


class Empresa(models.Model):
    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=30, unique=True)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'empresas'

    def __str__(self):
        return self.nombre


class Membresia(models.Model):
    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        OPERADOR = 'OPERADOR', 'Operador'
        LECTOR = 'LECTOR', 'Solo lectura'

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membresia')
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='membresias')
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.LECTOR)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'membresias'


class EmpresaQuerySet(models.QuerySet):
    def de_empresa(self, empresa):
        return self.filter(**{self.model.EMPRESA_LOOKUP: empresa})


class EmpresaModel(models.Model):
    """Base para modelos que pertenecen directamente a una empresa."""
    EMPRESA_LOOKUP = 'empresa'
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='+')
    objects = EmpresaQuerySet.as_manager()

    class Meta:
        abstract = True