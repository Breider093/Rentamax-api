from django.contrib import admin

from .models import Cliente, ClienteDocumento


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('documento', 'razon_social', 'ciudad', 'email', 'habilitado')
    list_filter = ('habilitado', 'tipo_documento', 'ciudad')
    search_fields = ('documento', 'razon_social', 'email')


@admin.register(ClienteDocumento)
class ClienteDocumentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'archivo', 'creado_en')
    list_filter = ('tipo',)
    search_fields = ('cliente__documento', 'cliente__razon_social')
