from django.db import transaction
from rest_framework import serializers

from .models import (
	Entrada, EntradaDetalle, Inventario, Lote, MovimientoInventario, OrdenCompra,
	OrdenCompraDetalle, Salida, SalidaDetalle,
)


class OrdenCompraDetalleSerializer(serializers.ModelSerializer):
	orden_compra = serializers.PrimaryKeyRelatedField(
		queryset=OrdenCompra.objects.all()
	)

	class Meta:
		model = OrdenCompraDetalle
		fields = '__all__'
		read_only_fields = ['subtotal', 'descripcion', 'cantidad_recibida']
		extra_kwargs = {'orden_compra': {'required': False}}

	def validate(self, attrs):
		if attrs.get('cantidad', 0) <= 0:
			raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
		if attrs.get('precio_unitario', 0) < 0:
			raise serializers.ValidationError({'precio_unitario': 'No puede ser negativo.'})
		return attrs


class OrdenCompraDetalleAnidadoSerializer(OrdenCompraDetalleSerializer):
	orden_compra = serializers.PrimaryKeyRelatedField(read_only=True)


class OrdenCompraSerializer(serializers.ModelSerializer):
	detalles = OrdenCompraDetalleAnidadoSerializer(many=True, required=False)

	class Meta:
		model = OrdenCompra
		fields = '__all__'
		read_only_fields = ['numero', 'subtotal', 'total', 'creado_en', 'actualizado_en', 'creado_por']

	def validate(self, attrs):
		fecha = attrs.get('fecha_entrega_programada')
		fecha_emision = attrs.get('fecha_emision', getattr(self.instance, 'fecha_emision', None))
		if fecha and fecha_emision and fecha < fecha_emision:
			raise serializers.ValidationError({'fecha_entrega_programada': 'No puede ser anterior a la fecha de emisión.'})
		return attrs

	@transaction.atomic
	def create(self, validated_data):
		detalles = validated_data.pop('detalles', [])
		orden = OrdenCompra.objects.create(**validated_data)
		for detalle in detalles:
			OrdenCompraDetalle.objects.create(orden_compra=orden, **detalle)
		orden.recalcular_totales()
		return orden


class EntradaDetalleSerializer(serializers.ModelSerializer):
	entrada = serializers.PrimaryKeyRelatedField(queryset=Entrada.objects.all())
	precio = serializers.DecimalField(source='precio_unitario', max_digits=14, decimal_places=2, required=False)

	class Meta:
		model = EntradaDetalle
		fields = '__all__'
		read_only_fields = ['subtotal']
		extra_kwargs = {'entrada': {'required': False}}

	def validate(self, attrs):
		if attrs.get('cantidad', 0) <= 0:
			raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
		if attrs.get('precio_unitario', 0) < 0:
			raise serializers.ValidationError({'precio_unitario': 'No puede ser negativo.'})
		return attrs


class EntradaDetalleAnidadoSerializer(EntradaDetalleSerializer):
	entrada = serializers.PrimaryKeyRelatedField(read_only=True)


class EntradaSerializer(serializers.ModelSerializer):
	detalles = EntradaDetalleAnidadoSerializer(many=True, required=False)
	fecha = serializers.DateField(source='fecha_entrada', required=False)
	factura = serializers.CharField(source='numero_factura', required=False, allow_blank=True)

	class Meta:
		model = Entrada
		fields = '__all__'
		read_only_fields = ['numero', 'subtotal', 'total', 'creado_en']

	def validate(self, attrs):
		orden = attrs.get('orden_compra', getattr(self.instance, 'orden_compra', None))
		proveedor = attrs.get('proveedor', getattr(self.instance, 'proveedor', None))
		if orden and proveedor and orden.proveedor_id != proveedor.id:
			raise serializers.ValidationError({'proveedor': 'Debe coincidir con el proveedor de la orden.'})
		if orden and orden.estado in (OrdenCompra.Estado.CANCELADA, OrdenCompra.Estado.COMPLETADA):
			raise serializers.ValidationError({'orden_compra': 'La orden no admite nuevas entradas.'})
		return attrs

	@transaction.atomic
	def create(self, validated_data):
		detalles = validated_data.pop('detalles', [])
		entrada = Entrada.objects.create(**validated_data)
		for detalle in detalles:
			EntradaDetalle.objects.create(entrada=entrada, **detalle)
		entrada.recalcular_totales()
		return entrada


class InventarioSerializer(serializers.ModelSerializer):
	class Meta:
		model = Inventario
		fields = '__all__'
		read_only_fields = ['existencia', 'actualizado_en']


class SalidaDetalleSerializer(serializers.ModelSerializer):
	precio = serializers.DecimalField(source='precio_unitario', max_digits=14, decimal_places=2, required=False)

	class Meta:
		model = SalidaDetalle
		fields = '__all__'
		read_only_fields = ['subtotal', 'total_linea']

	def validate(self, attrs):
		if attrs.get('cantidad', 0) <= 0:
			raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
		if attrs.get('precio_unitario', 0) < 0 or attrs.get('iva_linea', 0) < 0:
			raise serializers.ValidationError('Los valores monetarios no pueden ser negativos.')
		return attrs


class SalidaDetalleAnidadoSerializer(SalidaDetalleSerializer):
	salida = serializers.PrimaryKeyRelatedField(read_only=True)


class SalidaSerializer(serializers.ModelSerializer):
	detalles = SalidaDetalleAnidadoSerializer(many=True, required=False)

	class Meta:
		model = Salida
		fields = '__all__'
		read_only_fields = ['numero', 'subtotal', 'total', 'creado_en']

	@transaction.atomic
	def create(self, validated_data):
		detalles = validated_data.pop('detalles', [])
		salida = Salida.objects.create(**validated_data)
		for detalle in detalles:
			SalidaDetalle.objects.create(salida=salida, **detalle)
		salida.recalcular_totales()
		return salida

	@transaction.atomic
	def update(self, instance, validated_data):
		detalles = validated_data.pop('detalles', None)
		salida = super().update(instance, validated_data)
		if detalles is not None:
			salida.detalles.all().delete()
			for detalle in detalles:
				SalidaDetalle.objects.create(salida=salida, **detalle)
			salida.recalcular_totales()
		return salida


class MovimientoInventarioSerializer(serializers.ModelSerializer):
	class Meta:
		model = MovimientoInventario
		fields = '__all__'
		read_only_fields = ['fecha']


class LoteSerializer(serializers.ModelSerializer):
	class Meta:
		model = Lote
		fields = '__all__'
		read_only_fields = ['cantidad_disponible']
