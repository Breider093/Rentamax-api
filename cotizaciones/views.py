from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from facturas.models import Factura, FacturaDetalle

from .models import Cotizacion, CotizacionDetalle
from .serializers import CotizacionDetalleSerializer, CotizacionSerializer


class CotizacionViewSet(viewsets.ModelViewSet):
	queryset = Cotizacion.objects.select_related('cliente', 'creado_por').prefetch_related(
		'detalles__producto'
	).all()
	serializer_class = CotizacionSerializer

	def get_queryset(self):
		queryset = super().get_queryset()
		cliente = self.request.query_params.get('cliente')
		estado = self.request.query_params.get('estado')
		if cliente:
			queryset = queryset.filter(cliente_id=cliente)
		if estado:
			queryset = queryset.filter(estado=estado)
		if self.request.query_params.get('vencidas') == 'true':
			queryset = queryset.filter(
				fecha_vencimiento__lt=timezone.localdate(),
				estado=Cotizacion.Estado.PENDIENTE,
			)
		return queryset

	def perform_create(self, serializer):
		serializer.save(
			creado_por=self.request.user if self.request.user.is_authenticated else None
		)

	def perform_update(self, serializer):
		if serializer.instance.estado != Cotizacion.Estado.PENDIENTE:
			raise serializers.ValidationError('Solo se pueden editar cotizaciones pendientes.')
		serializer.save()

	@action(detail=True, methods=['post'])
	def aprobar(self, request, pk=None):
		cotizacion = self.get_object()
		if cotizacion.estado != Cotizacion.Estado.PENDIENTE:
			return Response({'detail': 'Solo se pueden aprobar cotizaciones pendientes.'}, status=400)
		if not cotizacion.detalles.exists():
			return Response({'detail': 'La cotización debe tener al menos un producto.'}, status=400)
		cotizacion.estado = Cotizacion.Estado.APROBADA
		cotizacion.save(update_fields=['estado', 'actualizado_en'])
		return Response(self.get_serializer(cotizacion).data)

	@action(detail=True, methods=['post'])
	def rechazar(self, request, pk=None):
		cotizacion = self.get_object()
		if cotizacion.estado != Cotizacion.Estado.PENDIENTE:
			return Response({'detail': 'Solo se pueden rechazar cotizaciones pendientes.'}, status=400)
		cotizacion.estado = Cotizacion.Estado.RECHAZADA
		cotizacion.save(update_fields=['estado', 'actualizado_en'])
		return Response(self.get_serializer(cotizacion).data)

	@action(detail=True, methods=['post'])
	def cancelar(self, request, pk=None):
		cotizacion = self.get_object()
		if cotizacion.estado in (Cotizacion.Estado.APROBADA, Cotizacion.Estado.CANCELADA):
			return Response({'detail': 'La cotización no se puede cancelar en su estado actual.'}, status=400)
		cotizacion.estado = Cotizacion.Estado.CANCELADA
		cotizacion.save(update_fields=['estado', 'actualizado_en'])
		return Response(self.get_serializer(cotizacion).data)

	@action(detail=True, methods=['post'], url_path='convertir-factura')
	def convertir_factura(self, request, pk=None):
		with transaction.atomic():
			cotizacion = Cotizacion.objects.select_for_update().prefetch_related('detalles').get(pk=pk)
			if cotizacion.estado == Cotizacion.Estado.CONVERTIDA:
				return Response({'detail': 'La cotización ya fue convertida.'}, status=status.HTTP_400_BAD_REQUEST)
			if cotizacion.estado not in (Cotizacion.Estado.PENDIENTE, Cotizacion.Estado.APROBADA):
				return Response({'detail': 'La cotización no se puede convertir en su estado actual.'}, status=status.HTTP_400_BAD_REQUEST)
			if not cotizacion.detalles.exists():
				return Response({'detail': 'La cotización debe tener al menos un producto.'}, status=status.HTTP_400_BAD_REQUEST)

			factura = Factura.objects.create(
				numero=timezone.now().strftime('FAC-%Y%m%d-%H%M%S-%f'),
				cliente=cotizacion.cliente,
				cotizacion=cotizacion,
				fecha_emision=timezone.localdate(),
				impuestos=cotizacion.impuestos,
				observaciones=cotizacion.observaciones,
				creado_por=request.user if request.user.is_authenticated else None,
			)
			for detalle in cotizacion.detalles.all():
				FacturaDetalle.objects.create(
					factura=factura,
					producto=detalle.producto,
					descripcion=detalle.descripcion,
					cantidad=detalle.cantidad,
					precio_unitario=detalle.precio_unitario,
				)
			factura.recalcular_totales()
			cotizacion.estado = Cotizacion.Estado.CONVERTIDA
			cotizacion.save(update_fields=['estado', 'actualizado_en'])

		return Response({'factura': factura.id, 'cotizacion': self.get_serializer(cotizacion).data}, status=status.HTTP_201_CREATED)


class CotizacionDetalleViewSet(viewsets.ModelViewSet):
	queryset = CotizacionDetalle.objects.select_related('cotizacion', 'producto').all()
	serializer_class = CotizacionDetalleSerializer

	def perform_create(self, serializer):
		cotizacion = serializer.validated_data['cotizacion']
		if cotizacion.estado != Cotizacion.Estado.PENDIENTE:
			raise serializers.ValidationError('Solo se pueden modificar cotizaciones pendientes.')
		with transaction.atomic():
			serializer.save()
			cotizacion.recalcular_totales()

	def perform_update(self, serializer):
		if serializer.instance.cotizacion.estado != Cotizacion.Estado.PENDIENTE:
			raise serializers.ValidationError('Solo se pueden modificar cotizaciones pendientes.')
		with transaction.atomic():
			detalle = serializer.save()
			detalle.cotizacion.recalcular_totales()

	def perform_destroy(self, instance):
		if instance.cotizacion.estado != Cotizacion.Estado.PENDIENTE:
			raise serializers.ValidationError('Solo se pueden modificar cotizaciones pendientes.')
		cotizacion = instance.cotizacion
		with transaction.atomic():
			instance.delete()
			cotizacion.recalcular_totales()
