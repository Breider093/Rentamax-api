from django.db import transaction
from rest_framework import serializers

from .models import Devolucion, DevolucionDetalle


class DevolucionDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevolucionDetalle
        fields = '__all__'
        read_only_fields = ['total_kg']

    def validate(self, attrs):
        if attrs.get('cantidad', 0) <= 0:
            raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
        if attrs.get('peso_unitario', 0) < 0:
            raise serializers.ValidationError({'peso_unitario': 'No puede ser negativo.'})
        return attrs


class DevolucionDetalleAnidadoSerializer(DevolucionDetalleSerializer):
    devolucion = serializers.PrimaryKeyRelatedField(read_only=True)


class DevolucionSerializer(serializers.ModelSerializer):
    detalles = DevolucionDetalleAnidadoSerializer(many=True, required=False)

    class Meta:
        model = Devolucion
        fields = '__all__'
        read_only_fields = ['numero', 'creado_por', 'creado_en', 'actualizado_en']

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        obra = attrs.get('obra', getattr(self.instance, 'obra', None))
        factura = attrs.get('factura', getattr(self.instance, 'factura', None))
        precio = attrs.get('precio_transporte', getattr(self.instance, 'precio_transporte', 0))
        if cliente and not cliente.habilitado:
            raise serializers.ValidationError({'cliente': 'El cliente no está habilitado.'})
        if obra and cliente and obra.cliente_id != cliente.id:
            raise serializers.ValidationError({'obra': 'La obra debe pertenecer al cliente.'})
        if factura and factura.remision_id and factura.remision.cliente_id != cliente.id:
            raise serializers.ValidationError({'factura': 'La factura no pertenece al cliente.'})
        if precio < 0:
            raise serializers.ValidationError({'precio_transporte': 'No puede ser negativo.'})
        if factura and attrs.get('estado_factura') == Devolucion.EstadoFactura.SIN_FACTURA:
            raise serializers.ValidationError({'estado_factura': 'Una devolución con factura no puede estar sin factura.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles = validated_data.pop('detalles', [])
        devolucion = Devolucion.objects.create(**validated_data)
        for detalle in detalles:
            DevolucionDetalle.objects.create(devolucion=devolucion, **detalle)
        return devolucion

    @transaction.atomic
    def update(self, instance, validated_data):
        detalles = validated_data.pop('detalles', None)
        devolucion = super().update(instance, validated_data)
        if detalles is not None:
            devolucion.detalles.all().delete()
            for detalle in detalles:
                DevolucionDetalle.objects.create(devolucion=devolucion, **detalle)
        return devolucion
