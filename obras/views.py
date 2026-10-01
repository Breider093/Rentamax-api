from rest_framework import viewsets

from empresas.views import EmpresaQuerysetMixin
from .models import Obra
from .serializers import ObraSerializer


class ObraViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    # Queryset is tenant-scoped by EmpresaQuerysetMixin.
    serializer_class = ObraSerializer
    queryset = Obra.objects.select_related('cliente').all()

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        return queryset
