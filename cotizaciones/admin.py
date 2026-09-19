from django.contrib import admin

from .models import Cotizacion, CotizacionDetalle


class CotizacionDetalleInline(admin.TabularInline):
	model = CotizacionDetalle
	extra = 0


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
	list_display = ('numero', 'cliente', 'fecha_emision', 'fecha_vencimiento', 'estado', 'total')
	list_filter = ('estado', 'fecha_emision', 'fecha_vencimiento')
	search_fields = ('numero', 'cliente__razon_social', 'cliente__documento')
	inlines = [CotizacionDetalleInline]


@admin.register(CotizacionDetalle)
class CotizacionDetalleAdmin(admin.ModelAdmin):
	list_display = ('cotizacion', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
	search_fields = ('cotizacion__numero', 'producto__descripcion')
