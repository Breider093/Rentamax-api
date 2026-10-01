from rest_framework import serializers
from empresas.serializers import EmpresaSerializerMixin, TenantDownloadFileField
from .models import Producto, ProductoProveedor, Proveedor, TipoProducto


class TipoProductoSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = ['id', 'nombre']


class ProductoSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    manual = TenantDownloadFileField(url_name='producto-manual', required=False, allow_null=True)
    ficha_tecnica = TenantDownloadFileField(
        url_name='producto-ficha-tecnica', required=False, allow_null=True,
    )

    class Meta:
        model = Producto
        fields = [
            'id',
            'descripcion',
            'tipo_producto',
            'peso_kg',
            'precio_alquiler',
            'precio_reposicion',
            'manual',
            'ficha_tecnica',
            'fecha_creacion',
            'fecha_actualizacion',
        ]


class ProveedorSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'nit', 'direccion', 'telefono', 'email']


class ProductoProveedorSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ProductoProveedor
        fields = [
            'id',
            'producto',
            'proveedor',
            'costo_subarriendo',
            'vinculo_habilitado',
        ]