from django.contrib import admin

from .models import (
	Entrada, EntradaDetalle, Inventario, Lote, MovimientoInventario, OrdenCompra,
	OrdenCompraDetalle, Salida, SalidaDetalle,
)


class OrdenCompraDetalleInline(admin.TabularInline):
	model = OrdenCompraDetalle
	extra = 0


class EntradaDetalleInline(admin.TabularInline):
	model = EntradaDetalle
	extra = 0


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
	list_display = ('numero', 'proveedor', 'fecha_emision', 'estado', 'total')
	list_filter = ('estado', 'fecha_emision')
	search_fields = ('numero', 'proveedor__nombre')
	inlines = [OrdenCompraDetalleInline]


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
	list_display = ('numero', 'proveedor', 'orden_compra', 'fecha_entrada', 'estado', 'total')
	list_filter = ('estado', 'fecha_entrada')
	search_fields = ('numero', 'numero_factura', 'proveedor__nombre')
	inlines = [EntradaDetalleInline]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
	list_display = ('producto', 'existencia', 'actualizado_en')
	search_fields = ('producto__descripcion',)


class SalidaDetalleInline(admin.TabularInline):
	model = SalidaDetalle
	extra = 0


@admin.register(Salida)
class SalidaAdmin(admin.ModelAdmin):
	list_display = ('numero', 'fecha', 'tipo', 'cliente', 'estado', 'total')
	list_filter = ('tipo', 'estado', 'fecha')
	search_fields = ('numero', 'cliente__razon_social')
	inlines = [SalidaDetalleInline]


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
	list_display = ('producto', 'tipo', 'cantidad', 'referencia_tipo', 'referencia_id', 'fecha')
	list_filter = ('tipo', 'fecha')
	search_fields = ('producto__descripcion', 'referencia_tipo')


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
	list_display = ('producto', 'codigo', 'fecha_vencimiento', 'cantidad_disponible')
	search_fields = ('producto__descripcion', 'codigo')
