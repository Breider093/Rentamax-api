from django.contrib import admin

from .models import Devolucion, DevolucionDetalle


class DevolucionDetalleInline(admin.TabularInline):
    model = DevolucionDetalle
    extra = 0


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'factura', 'estado', 'estado_factura', 'creado_en')
    list_filter = ('estado', 'estado_factura', 'creado_en')
    search_fields = ('numero', 'cliente__razon_social', 'factura__numero')
    inlines = [DevolucionDetalleInline]


@admin.register(DevolucionDetalle)
class DevolucionDetalleAdmin(admin.ModelAdmin):
    list_display = ('devolucion', 'producto', 'cantidad', 'motivo', 'total_kg')
    list_filter = ('motivo',)
    search_fields = ('devolucion__numero', 'producto__descripcion')
