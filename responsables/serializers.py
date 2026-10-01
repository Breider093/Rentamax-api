from rest_framework import serializers

from empresas.serializers import EmpresaSerializerMixin
from .models import Responsable


class ResponsableSerializer(EmpresaSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Responsable
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
