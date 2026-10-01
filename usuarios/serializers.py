from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UsuarioPerfil
from empresas.models import Membresia


User = get_user_model()


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioPerfil
        fields = ['documento', 'telefono', 'cargo', 'estado']


class UsuarioSerializer(serializers.ModelSerializer):
    perfil = UsuarioPerfilSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    rol = serializers.ChoiceField(
        choices=Membresia.Rol.choices,
        required=False,
        default=Membresia.Rol.OPERADOR,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'is_active', 'perfil', 'rol',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        perfil_data = validated_data.pop('perfil', {})
        validated_data.pop('rol', None)
        password = validated_data.pop('password', None)
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        usuario = User(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        UsuarioPerfil.objects.update_or_create(usuario=usuario, defaults=perfil_data)
        return usuario

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', None)
        validated_data.pop('rol', None)
        password = validated_data.pop('password', None)
        instance.is_staff = False
        instance.is_superuser = False
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        if perfil_data is not None:
            UsuarioPerfil.objects.update_or_create(usuario=instance, defaults=perfil_data)
        return instance
