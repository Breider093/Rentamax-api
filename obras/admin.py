from django.contrib import admin

from .models import Obra


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente', 'direccion', 'estado', 'creado_en')
    list_filter = ('estado', 'cliente')
    search_fields = ('nombre', 'direccion', 'cliente__documento', 'cliente__razon_social')
