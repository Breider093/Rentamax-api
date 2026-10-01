from django.core.exceptions import FieldDoesNotExist
from rest_framework import serializers
from rest_framework.reverse import reverse


class EmpresaSerializerMixin:
    """Oculta la empresa en entradas y limita relaciones al tenant activo."""

    def _has_empresa_directa(self):
        model = getattr(getattr(self, 'Meta', None), 'model', None)
        if model is None:
            return False
        try:
            field = model._meta.get_field('empresa')
        except FieldDoesNotExist:
            return False
        related_model = getattr(getattr(field, 'remote_field', None), 'model', None)
        return bool(
            field.is_relation
            and related_model is not None
            and related_model._meta.label_lower == 'empresas.empresa'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self._has_empresa_directa():
            fields.pop('empresa', None)

        request = self.context.get('request')
        empresa = getattr(request, 'empresa', None)
        for field in fields.values():
            relation = getattr(field, 'child_relation', field)
            queryset = getattr(relation, 'queryset', None)
            if queryset is not None and hasattr(queryset.model, 'EMPRESA_LOOKUP'):
                relation.queryset = (
                    queryset.de_empresa(empresa) if empresa is not None else queryset.none()
                )
        return fields

    def save(self, **kwargs):
        if self.instance is None and self._has_empresa_directa():
            request = self.context.get('request')
            empresa = getattr(request, 'empresa', None)
            if empresa is not None:
                kwargs['empresa'] = empresa
            elif 'empresa' not in kwargs:
                raise serializers.ValidationError(
                    {'empresa': 'No se puede crear el registro sin una empresa activa.'}
                )
        return super().save(**kwargs)


class TenantDownloadFileField(serializers.FileField):
    """Accepts uploads but represents stored files with an authorized API URL."""

    def __init__(self, *args, url_name, **kwargs):
        self.url_name = url_name
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if not value:
            return None
        instance = getattr(self.parent, 'instance', None)
        if instance is None or instance.pk is None:
            return None
        return reverse(
            self.url_name,
            kwargs={'pk': instance.pk},
            request=self.context.get('request'),
        )
