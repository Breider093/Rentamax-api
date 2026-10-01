from django.shortcuts import render


class EmpresaQuerysetMixin:
	"""Limita todos los viewsets tenant-aware a la empresa autenticada."""

	def get_queryset(self):
		queryset = super().get_queryset()
		empresa = getattr(self.request, 'empresa', None)
		if not hasattr(queryset, 'de_empresa'):
			return queryset.none()
		return queryset.de_empresa(empresa) if empresa is not None else queryset.none()
