from rest_framework import serializers

from .models import EquipoObra, Prestamo, PrestamoDetalle


class PrestamoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrestamoDetalle
        fields = [
            'id',
            'prestamo',
            'producto',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]
        read_only_fields = ['subtotal']

    def validate(self, attrs):
        producto = attrs.get('producto')
        if not producto:
            raise serializers.ValidationError('Debes indicar un producto.')
        return attrs


class PrestamoSerializer(serializers.ModelSerializer):
    detalles = PrestamoDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = Prestamo
        fields = [
            'id',
            'cliente',
            'obra',
            'fecha_reserva',
            'fecha_entrega',
            'estado',
            'total',
            'total_pagado',
            'observacion',
            'detalles',
        ]
        read_only_fields = ['total', 'detalles']

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        obra = attrs.get('obra', getattr(self.instance, 'obra', None))
        if obra and cliente and obra.cliente_id != cliente.id:
            raise serializers.ValidationError({
                'obra': 'La obra debe pertenecer al cliente del préstamo.'
            })
        return attrs


class EquipoObraSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipoObra
        fields = '__all__'

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        obra = attrs.get('obra', getattr(self.instance, 'obra', None))
        if cliente and obra and obra.cliente_id != cliente.id:
            raise serializers.ValidationError({
                'obra': 'La obra debe pertenecer al cliente indicado.',
            })
        return attrs
