from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Cotizacion, CotizacionDetalle


class CotizacionDetalleSerializer(serializers.ModelSerializer):
	class Meta:
		model = CotizacionDetalle
		fields = '__all__'
		read_only_fields = ['subtotal', 'total_linea', 'descripcion']

	def validate(self, attrs):
		if attrs.get('cantidad', 0) <= 0:
			raise serializers.ValidationError({'cantidad': 'Debe ser mayor que cero.'})
		if attrs.get('precio_unitario', 0) < 0:
			raise serializers.ValidationError({'precio_unitario': 'No puede ser negativo.'})
		if attrs.get('iva_linea', 0) < 0:
			raise serializers.ValidationError({'iva_linea': 'No puede ser negativo.'})
		return attrs


class CotizacionDetalleAnidadoSerializer(CotizacionDetalleSerializer):
	cotizacion = serializers.PrimaryKeyRelatedField(read_only=True)


class CotizacionSerializer(serializers.ModelSerializer):
	detalles = CotizacionDetalleAnidadoSerializer(many=True, required=False)

	class Meta:
		model = Cotizacion
		fields = '__all__'
		read_only_fields = [
			'numero', 'subtotal', 'total', 'creado_por', 'creado_en', 'actualizado_en',
		]

	def validate(self, attrs):
		cliente = attrs.get('cliente', getattr(self.instance, 'cliente', None))
		fecha_emision = attrs.get(
			'fecha_emision', getattr(self.instance, 'fecha_emision', timezone.localdate())
		)
		fecha_vencimiento = attrs.get('fecha_vencimiento')
		vigencia_dias = attrs.get('vigencia_dias', getattr(self.instance, 'vigencia_dias', 30))
		if cliente and not cliente.habilitado:
			raise serializers.ValidationError({'cliente': 'El cliente no está habilitado.'})
		if fecha_vencimiento and fecha_vencimiento < fecha_emision:
			raise serializers.ValidationError({
				'fecha_vencimiento': 'No puede ser anterior a la fecha de emisión.'
			})
		if vigencia_dias <= 0:
			raise serializers.ValidationError({'vigencia_dias': 'Debe ser mayor que cero.'})
		if not fecha_vencimiento:
			attrs['fecha_vencimiento'] = fecha_emision + timedelta(days=vigencia_dias)
		return attrs

	@transaction.atomic
	def create(self, validated_data):
		detalles = validated_data.pop('detalles', [])
		cotizacion = Cotizacion.objects.create(**validated_data)
		for detalle in detalles:
			CotizacionDetalle.objects.create(cotizacion=cotizacion, **detalle)
		cotizacion.recalcular_totales()
		return cotizacion

	@transaction.atomic
	def update(self, instance, validated_data):
		detalles = validated_data.pop('detalles', None)
		cotizacion = super().update(instance, validated_data)
		if detalles is not None:
			cotizacion.detalles.all().delete()
			for detalle in detalles:
				CotizacionDetalle.objects.create(cotizacion=cotizacion, **detalle)
		cotizacion.recalcular_totales()
		return cotizacion
