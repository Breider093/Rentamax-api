from django.db import transaction
from rest_framework import serializers
from django.utils import timezone

from .models import Remision, RemisionAlarma, RemisionDetalle, RemisionReserva


class RemisionDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemisionDetalle
        fields = '__all__'
        read_only_fields = ['subtotal', 'descripcion']
        extra_kwargs = {'remision': {'required': False}}

    def validate(self, attrs):
        producto = attrs.get('producto', getattr(self.instance, 'producto', None))
        cantidad = attrs.get('cantidad', getattr(self.instance, 'cantidad', None))
        precio = attrs.get('precio_unitario', getattr(self.instance, 'precio_unitario', None))
        if cantidad is not None and cantidad <= 0:
            raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
        if precio is not None and precio < 0:
            raise serializers.ValidationError({'precio_unitario': 'No puede ser negativo.'})
        if producto and not attrs.get('descripcion'):
            attrs['descripcion'] = producto.descripcion
        return attrs


class RemisionSerializer(serializers.ModelSerializer):
    detalles = RemisionDetalleSerializer(many=True, required=False)
    tiene_factura = serializers.SerializerMethodField()

    class Meta:
        model = Remision
        fields = [
            'id', 'numero', 'cliente', 'transportador', 'fecha_emision',
            'fecha_entrega_programada', 'fecha_entrega_real', 'estado',
            'prioridad', 'observaciones', 'subtotal', 'impuestos', 'total',
            'creado_en', 'actualizado_en', 'detalles', 'tiene_factura',
        ]
        read_only_fields = [
            'numero', 'subtotal', 'total', 'creado_en', 'actualizado_en',
            'tiene_factura',
        ]

    def get_tiene_factura(self, obj):
        return hasattr(obj, 'factura')

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        if cliente and not cliente.habilitado:
            raise serializers.ValidationError({'cliente': 'El cliente no está habilitado.'})
        fecha = attrs.get('fecha_entrega_programada')
        fecha_emision = attrs.get(
            'fecha_emision',
            getattr(self.instance, 'fecha_emision', timezone.localdate()),
        )
        if fecha and fecha_emision > fecha:
            raise serializers.ValidationError({
                'fecha_entrega_programada': 'No puede ser anterior a la fecha de emisión.'
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles = validated_data.pop('detalles', [])
        remision = Remision.objects.create(**validated_data)
        for detalle in detalles:
            RemisionDetalle.objects.create(remision=remision, **detalle)
        remision.recalcular_totales()
        return remision


class RemisionReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemisionReserva
        fields = '__all__'
        read_only_fields = ['confirmada_at', 'cancelada_at', 'creado_en']


class RemisionAlarmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemisionAlarma
        fields = '__all__'
        read_only_fields = ['resuelta_at', 'creado_en']
