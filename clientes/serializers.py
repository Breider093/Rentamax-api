from rest_framework import serializers

from .models import Cliente, ClienteDocumento


class ClienteDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClienteDocumento
        fields = ['id', 'cliente', 'tipo', 'archivo', 'creado_en']
        read_only_fields = ['creado_en']


class ClienteSerializer(serializers.ModelSerializer):
    documentos = ClienteDocumentoSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id',
            'documento',
            'tipo_documento',
            'razon_social',
            'direccion',
            'ciudad',
            'email',
            'telefono',
            'celular',
            'habilitado',
            'documentos',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = ['creado_en', 'actualizado_en', 'documentos']
