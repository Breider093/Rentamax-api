from django.contrib import admin

from .models import KardexDetalle, KardexMovimiento


@admin.register(KardexMovimiento)
class KardexMovimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'obra', 'tipo', 'valor', 'estado')
    list_filter = ('tipo', 'estado')
    search_fields = ('cliente__documento', 'cliente__razon_social', 'numero_documento')


@admin.register(KardexDetalle)
class KardexDetalleAdmin(admin.ModelAdmin):
    list_display = ('movimiento', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('producto',)
