from django.db import models
from empresas.models import EmpresaModel, EmpresaQuerySet


class TipoProducto(EmpresaModel):
    nombre = models.CharField(
        max_length=100,
    )

    class Meta:
        db_table = 'tipo_producto'
        verbose_name = 'Tipo de Producto'
        verbose_name_plural = 'Tipos de Producto'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nombre'], name='tipo_producto_empresa_nombre_uq'),
        ]

    def __str__(self):
        return self.nombre


class Producto(EmpresaModel):
    codigo = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=255)

    tipo_producto = models.ForeignKey(
        TipoProducto,
        on_delete=models.PROTECT,
        related_name='productos'
    )

    proveedores = models.ManyToManyField(
        'Proveedor',
        through='ProductoProveedor',
        related_name='productos'
    )

    peso_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    precio_alquiler = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    precio_reposicion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    manual = models.FileField(
        upload_to='productos/manuales/',
        blank=True,
        null=True
    )

    ficha_tecnica = models.FileField(
        upload_to='productos/fichas_tecnicas/',
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['descripcion']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'codigo'], name='producto_empresa_codigo_uq'),
        ]

    def __str__(self):
        return self.descripcion


class Proveedor(EmpresaModel):
    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=30, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'proveedor'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nit'], name='proveedor_empresa_nit_uq'),
        ]

    def __str__(self):
        return self.nombre


class ProductoProveedor(models.Model):
    EMPRESA_LOOKUP = 'producto__empresa'
    objects = EmpresaQuerySet.as_manager()

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='proveedores_relacion'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='productos_relacion'
    )
    costo_subarriendo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    vinculo_habilitado = models.BooleanField(default=True)

    class Meta:
        db_table = 'producto_proveedor'
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'proveedor'],
                name='producto_proveedor_unico'
            )
        ]