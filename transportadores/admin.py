from django.contrib import admin

from .models import Transportador, TransportadorVehiculo, Vehiculo, Viaje, ViajeRemision


@admin.register(Transportador)
class TransportadorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'documento', 'telefono', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre', 'documento', 'licencia_numero')


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'tipo', 'marca', 'modelo', 'estado')
    list_filter = ('tipo', 'estado')
    search_fields = ('placa', 'marca', 'modelo')


@admin.register(TransportadorVehiculo)
class TransportadorVehiculoAdmin(admin.ModelAdmin):
    list_display = ('transportador', 'vehiculo', 'es_principal', 'fecha_asignacion', 'fecha_desasignacion')
    list_filter = ('es_principal',)


@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'transportador', 'vehiculo', 'destino', 'fecha_salida', 'estado')
    list_filter = ('estado', 'pais_destino')
    search_fields = ('codigo', 'destino', 'transportador__nombre')


@admin.register(ViajeRemision)
class ViajeRemisionAdmin(admin.ModelAdmin):
    list_display = ('viaje', 'remision', 'orden_entrega', 'estado')
    list_filter = ('estado',)
