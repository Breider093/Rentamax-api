from rest_framework import serializers

from .models import KardexDetalle, KardexMovimiento


class KardexDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KardexDetalle
        fields = [
            'id',
            'movimiento',
            'producto',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]
        read_only_fields = ['subtotal']

    def validate(self, attrs):
        return attrs


class KardexMovimientoSerializer(serializers.ModelSerializer):
    detalles = KardexDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = KardexMovimiento
        fields = [
            'id',
            'cliente',
            'obra',
            'remision',
            'tipo',
            'numero_documento',
            'fecha',
            'descripcion',
            'valor',
            'estado',
            'detalles',
        ]
        read_only_fields = ['fecha', 'detalles']

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        obra = attrs.get('obra', getattr(self.instance, 'obra', None))
        if obra and cliente and obra.cliente_id != cliente.id:
            raise serializers.ValidationError({
                'obra': 'La obra debe pertenecer al cliente del movimiento.'
            })
        return attrs
