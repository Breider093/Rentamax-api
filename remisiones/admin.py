from django.contrib import admin

from .models import Remision, RemisionAlarma, RemisionDetalle, RemisionReserva


class RemisionDetalleInline(admin.TabularInline):
    model = RemisionDetalle
    extra = 0


@admin.register(Remision)
class RemisionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha_entrega_programada', 'estado', 'prioridad', 'total')
    list_filter = ('empresa', 'estado', 'prioridad')
    search_fields = ('numero', 'cliente__razon_social', 'cliente__documento')
    inlines = [RemisionDetalleInline]


@admin.register(RemisionReserva)
class RemisionReservaAdmin(admin.ModelAdmin):
    list_display = ('remision', 'fecha_reserva', 'estado')
    list_filter = ('remision__empresa', 'estado')


@admin.register(RemisionAlarma)
class RemisionAlarmaAdmin(admin.ModelAdmin):
    list_display = ('remision', 'tipo', 'prioridad', 'estado', 'fecha_limite')
    list_filter = ('remision__empresa', 'tipo', 'prioridad', 'estado')
