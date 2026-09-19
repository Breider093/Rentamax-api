from django.contrib import admin

from .models import Prestamo, PrestamoDetalle


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'obra', 'fecha_reserva', 'estado', 'total', 'total_pagado')
    list_filter = ('estado', 'fecha_reserva')
    search_fields = ('cliente__documento', 'cliente__razon_social', 'obra__nombre')


@admin.register(PrestamoDetalle)
class PrestamoDetalleAdmin(admin.ModelAdmin):
    list_display = ('prestamo', 'producto', 'cantidad', 'subtotal')
    list_filter = ('producto',)
