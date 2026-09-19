from django.db import transaction
from rest_framework import serializers

from .models import Factura, FacturaDetalle, FacturaPago


class FacturaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacturaDetalle
        fields = '__all__'
        read_only_fields = ['subtotal', 'descripcion']

    def validate(self, attrs):
        if attrs.get('cantidad', 0) <= 0:
            raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
        if attrs.get('precio_unitario', 0) < 0:
            raise serializers.ValidationError({'precio_unitario': 'No puede ser negativo.'})
        return attrs


class FacturaDetalleAnidadoSerializer(FacturaDetalleSerializer):
    factura = serializers.PrimaryKeyRelatedField(read_only=True)


class FacturaSerializer(serializers.ModelSerializer):
    detalles = FacturaDetalleAnidadoSerializer(many=True, required=False)
    saldo_pendiente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'
        extra_kwargs = {'cliente': {'required': False}}
        read_only_fields = [
            'subtotal', 'total', 'numero', 'creado_por', 'creado_en', 'actualizado_en',
            'saldo_pendiente',
        ]

    def validate_remision(self, remision):
        if remision.estado in (remision.Estado.CANCELADA, remision.Estado.PENDIENTE):
            raise serializers.ValidationError('La remisión no está habilitada para facturación.')
        if hasattr(remision, 'factura') and (not self.instance or remision.factura.pk != self.instance.pk):
            raise serializers.ValidationError('La remisión ya tiene una factura.')
        return remision

    def validate(self, attrs):
        cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
        remision = attrs.get('remision', getattr(self.instance, 'remision', None))
        if not cliente and not remision:
            raise serializers.ValidationError({'cliente': 'La factura directa debe tener un cliente.'})
        if cliente and not cliente.habilitado:
            raise serializers.ValidationError({'cliente': 'El cliente no está habilitado.'})
        if remision and cliente and remision.cliente_id != cliente.id:
            raise serializers.ValidationError({'remision': 'La remisión no pertenece al cliente.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles = validated_data.pop('detalles', [])
        remision = validated_data.get('remision')
        if remision:
            validated_data.setdefault('cliente', remision.cliente)
        factura = Factura.objects.create(**validated_data)
        if remision and not detalles:
            detalles = [
                {
                    'producto': detalle.producto,
                    'descripcion': detalle.descripcion,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': detalle.precio_unitario,
                }
                for detalle in remision.detalles.all()
            ]
        for detalle in detalles:
            FacturaDetalle.objects.create(factura=factura, **detalle)
        if detalles:
            factura.recalcular_totales()
        elif remision:
            factura.subtotal = remision.subtotal
            factura.impuestos = remision.impuestos
            factura.total = remision.total
            factura.save(update_fields=['subtotal', 'impuestos', 'total', 'actualizado_en'])
        return factura

    @transaction.atomic
    def update(self, instance, validated_data):
        detalles = validated_data.pop('detalles', None)
        factura = super().update(instance, validated_data)
        if detalles is not None:
            factura.detalles.all().delete()
            for detalle in detalles:
                FacturaDetalle.objects.create(factura=factura, **detalle)
            factura.recalcular_totales()
        return factura


class FacturaPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacturaPago
        fields = '__all__'
        read_only_fields = ['fecha_pago']

    def validate_monto(self, monto):
        if monto <= 0:
            raise serializers.ValidationError('El monto debe ser mayor que cero.')
        return monto
