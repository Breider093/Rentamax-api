from django.contrib import admin

from .models import Factura, FacturaDetalle, FacturaPago

class FacturaDetalleInline(admin.TabularInline):
    model = FacturaDetalle
    extra = 0

class FacturaPagoInline(admin.TabularInline):
    model = FacturaPago
    extra = 0

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'remision', 'fecha_emision', 'estado', 'total', 'saldo_pendiente')
    list_filter = ('estado', 'metodo_pago', 'fecha_emision')
    search_fields = ('numero', 'cliente__razon_social', 'cliente__documento')
    inlines = [FacturaDetalleInline, FacturaPagoInline]

@admin.register(FacturaDetalle)
class FacturaDetalleAdmin(admin.ModelAdmin):
    list_display = ('factura', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('factura__numero', 'producto__descripcion')

@admin.register(FacturaPago)
class FacturaPagoAdmin(admin.ModelAdmin):
    list_display = ('factura', 'metodo_pago', 'monto', 'fecha_pago', 'referencia')
    list_filter = ('metodo_pago', 'fecha_pago')
    search_fields = ('factura__numero', 'referencia')

