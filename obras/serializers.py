from rest_framework import serializers

from .models import Obra


class ObraSerializer(serializers.ModelSerializer):
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
