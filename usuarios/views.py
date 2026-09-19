from django.contrib.auth import get_user_model
from rest_framework import viewsets

from .serializers import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.select_related('perfil').all()
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(perfil__estado=estado)
        return queryset
