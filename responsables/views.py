from rest_framework import viewsets

from empresas.views import EmpresaQuerysetMixin
from .models import Responsable
from .serializers import ResponsableSerializer


class ResponsableViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    # The mixin applies the active company to this queryset.
    queryset = Responsable.objects.all()
    serializer_class = ResponsableSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset
