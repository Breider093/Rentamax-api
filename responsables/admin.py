from django.contrib import admin

from .models import Responsable


@admin.register(Responsable)
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ('documento', 'nombre', 'apellido', 'celular', 'estado')
    list_filter = ('estado',)
    search_fields = ('documento', 'nombre', 'apellido')
