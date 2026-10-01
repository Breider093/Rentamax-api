from django.db import models
from empresas.models import EmpresaModel, EmpresaQuerySet


class Cliente(EmpresaModel):
    documento = models.CharField(max_length=27)
    tipo_documento = models.CharField(max_length=20, blank=True)
    razon_social = models.CharField(max_length=150)
    direccion = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=50)
    email = models.EmailField(max_length=70)
    telefono = models.CharField(max_length=20, blank=True)
    celular = models.CharField(max_length=20)
    habilitado = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['razon_social']
        indexes = [
            models.Index(fields=['razon_social'], name='clientes_razon_social_idx'),
            models.Index(fields=['habilitado'], name='clientes_habilitado_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'documento'], name='cliente_empresa_doc_uq'),
        ]

    def __str__(self):
        return f'{self.razon_social} ({self.documento})'


class ClienteDocumento(models.Model):
    EMPRESA_LOOKUP = 'cliente__empresa'
    objects = EmpresaQuerySet.as_manager()

    class Tipo(models.TextChoices):
        RUT = 'rut', 'RUT'
        CEDULA_REPRESENTANTE = 'cedula_repr', 'Cédula del representante'
        CONTRATO_ALQUILER = 'contrato_alquiler', 'Contrato de alquiler'
        CAMARA_COMERCIO = 'camara_comercio', 'Cámara de comercio'
        CERTIFICADO_BANCARIO = 'certificado_bancario', 'Certificado bancario'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='documentos',
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    archivo = models.FileField(upload_to='clientes/documentos/')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cliente_documentos'
        verbose_name = 'Documento del cliente'
        verbose_name_plural = 'Documentos de clientes'
        ordering = ['tipo']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'tipo'],
                name='cliente_documento_tipo_unico',
            ),
        ]

    def __str__(self):
        return f'{self.cliente} - {self.get_tipo_display()}'
