from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from empresas.models import Membresia
from .serializers import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.select_related('perfil').all()
    serializer_class = UsuarioSerializer
    solo_admin = True

    def get_queryset(self):
        queryset = super().get_queryset().filter(membresia__empresa=self.request.empresa)
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(perfil__estado=estado)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        usuario = serializer.save()
        Membresia.objects.create(
            usuario=usuario,
            empresa=self.request.empresa,
            rol=serializer.validated_data.get('rol', Membresia.Rol.OPERADOR),
        )

    @transaction.atomic
    def perform_update(self, serializer):
        rol = serializer.validated_data.get('rol')
        usuario = serializer.save()
        if rol is not None:
            Membresia.objects.filter(
                usuario=usuario,
                empresa=self.request.empresa,
            ).update(rol=rol)

    @action(detail=False, methods=['get'], url_path='me', solo_admin=False)
    def me(self, request):
        membresia = request.membresia
        return Response({
            'id': request.user.pk,
            'username': request.user.get_username(),
            'email': request.user.email,
            'empresa': {
                'id': membresia.empresa_id,
                'nombre': membresia.empresa.nombre,
                'nit': membresia.empresa.nit,
            },
            'rol': membresia.rol,
        })
