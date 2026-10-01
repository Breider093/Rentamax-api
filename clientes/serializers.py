from rest_framework import serializers
from rest_framework.reverse import reverse

from empresas.serializers import EmpresaSerializerMixin
from .models import Cliente, ClienteDocumento


class ClienteDocumentoSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    archivo = serializers.FileField(write_only=True)
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = ClienteDocumento
        fields = ['id', 'cliente', 'tipo', 'archivo', 'archivo_url', 'creado_en']
        read_only_fields = ['creado_en', 'archivo_url']

    def get_archivo_url(self, instance):
        if not instance.archivo:
            return None
        return reverse(
            'cliente-documento-archivo',
            kwargs={'pk': instance.pk},
            request=self.context.get('request'),
        )


class ClienteSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
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
