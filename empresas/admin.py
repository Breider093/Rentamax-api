from django.contrib import admin

from .models import Empresa, Membresia


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'nit', 'activa', 'creado_en')
	list_filter = ('activa',)
	search_fields = ('nombre', 'nit')


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
	list_display = ('usuario', 'empresa', 'rol', 'activo')
	list_filter = ('empresa', 'rol', 'activo')
	search_fields = ('usuario__username', 'usuario__email', 'empresa__nombre', 'empresa__nit')

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		usuario = obj.usuario
		if usuario.is_staff:
			usuario.is_staff = False
			usuario.save(update_fields=['is_staff'])
