from rest_framework import serializers

from empresas.serializers import EmpresaSerializerMixin
from .models import Obra


class ObraSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Obra
        fields = [
            'id',
            'cliente',
            'nombre',
            'direccion',
            'telefono',
            'estado',
            'creado_en',
        ]
        read_only_fields = ['creado_en']
