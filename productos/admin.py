from django.contrib import admin

from .models import Producto, ProductoProveedor, Proveedor, TipoProducto


@admin.register(TipoProducto)
class TipoProductoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'empresa')
	list_filter = ('empresa',)
	search_fields = ('nombre', 'empresa__nombre', 'empresa__nit')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('codigo', 'descripcion', 'tipo_producto', 'empresa')
	list_filter = ('empresa', 'tipo_producto')
	search_fields = ('codigo', 'descripcion', 'empresa__nombre')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'nit', 'empresa')
	list_filter = ('empresa',)
	search_fields = ('nombre', 'nit', 'empresa__nombre')


@admin.register(ProductoProveedor)
class ProductoProveedorAdmin(admin.ModelAdmin):
	list_display = ('producto', 'proveedor', 'costo_subarriendo', 'vinculo_habilitado')
	list_filter = ('producto__empresa', 'vinculo_habilitado')
	search_fields = ('producto__descripcion', 'proveedor__nombre')
