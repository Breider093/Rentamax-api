from rest_framework import serializers
from .models import Producto, ProductoProveedor, Proveedor, TipoProducto


class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProducto
        fields = ['id', 'nombre']


class ProductoSerializer(serializers.ModelSerializer):
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


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'nit', 'direccion', 'telefono', 'email']


class ProductoProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoProveedor
        fields = [
            'id',
            'producto',
            'proveedor',
            'costo_subarriendo',
            'vinculo_habilitado',
        ]