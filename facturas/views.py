from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Factura, FacturaDetalle, FacturaPago
from .serializers import FacturaDetalleSerializer, FacturaPagoSerializer, FacturaSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.select_related('cliente', 'remision', 'creado_por').prefetch_related(
        'detalles__producto', 'pagos'
    ).all()
    serializer_class = FacturaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        cliente = self.request.query_params.get('cliente')
        sin_remision = self.request.query_params.get('sin_remision')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        if estado:
            queryset = queryset.filter(estado=estado)
        if sin_remision == 'true':
            queryset = queryset.filter(remision__isnull=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        if serializer.instance.estado in (Factura.Estado.PAGADA, Factura.Estado.ANULADA):
            raise serializers.ValidationError('La factura no se puede modificar en su estado actual.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def pagar(self, request, pk=None):
        with transaction.atomic():
            factura = Factura.objects.select_for_update().get(pk=pk)
            if factura.estado in (Factura.Estado.ANULADA, Factura.Estado.PAGADA):
                return Response({'detail': 'La factura no admite pagos en su estado actual.'}, status=400)
            pago_serializer = FacturaPagoSerializer(data={**request.data, 'factura': factura.id})
            pago_serializer.is_valid(raise_exception=True)
            monto = pago_serializer.validated_data['monto']
            if monto > factura.saldo_pendiente:
                return Response({'detail': 'El pago supera el saldo pendiente.'}, status=400)
            pago = pago_serializer.save()
            factura.estado = Factura.Estado.PAGADA if factura.saldo_pendiente == Decimal('0.00') else Factura.Estado.EMITIDA
            factura.save(update_fields=['estado', 'actualizado_en'])
        return Response({
            'factura': self.get_serializer(factura).data,
            'pago': FacturaPagoSerializer(pago).data,
        })

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        factura = self.get_object()
        if factura.estado == Factura.Estado.PAGADA:
            return Response({'detail': 'Una factura pagada no se puede anular.'}, status=400)
        if factura.estado == Factura.Estado.ANULADA:
            return Response({'detail': 'La factura ya está anulada.'}, status=400)
        factura.estado = Factura.Estado.ANULADA
        factura.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(factura).data)

    @action(detail=True, methods=['post'])
    def vencer(self, request, pk=None):
        factura = self.get_object()
        if factura.estado not in (Factura.Estado.PENDIENTE, Factura.Estado.EMITIDA):
            return Response({'detail': 'La factura no se puede marcar como vencida en su estado actual.'}, status=400)
        factura.estado = Factura.Estado.VENCIDA
        factura.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(factura).data)


class FacturaDetalleViewSet(viewsets.ModelViewSet):
    queryset = FacturaDetalle.objects.select_related('factura', 'producto').all()
    serializer_class = FacturaDetalleSerializer

    def perform_create(self, serializer):
        factura = serializer.validated_data['factura']
        if factura.estado != Factura.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar facturas pendientes.')
        with transaction.atomic():
            serializer.save()
            factura.recalcular_totales()

    def perform_update(self, serializer):
        if serializer.instance.factura.estado != Factura.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar facturas pendientes.')
        with transaction.atomic():
            detalle = serializer.save()
            detalle.factura.recalcular_totales()

    def perform_destroy(self, instance):
        if instance.factura.estado != Factura.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar facturas pendientes.')
        factura = instance.factura
        with transaction.atomic():
            instance.delete()
            factura.recalcular_totales()


class FacturaPagoViewSet(viewsets.ModelViewSet):
    queryset = FacturaPago.objects.select_related('factura').all()
    serializer_class = FacturaPagoSerializer

    def perform_create(self, serializer):
        factura = serializer.validated_data['factura']
        if factura.estado in (Factura.Estado.ANULADA, Factura.Estado.PAGADA):
            raise serializers.ValidationError('La factura no admite pagos en su estado actual.')
        if serializer.validated_data['monto'] > factura.saldo_pendiente:
            raise serializers.ValidationError('El pago supera el saldo pendiente.')
        pago = serializer.save()
        if factura.saldo_pendiente == Decimal('0.00'):
            factura.estado = Factura.Estado.PAGADA
            factura.save(update_fields=['estado', 'actualizado_en'])

    def get_queryset(self):
        queryset = super().get_queryset()
        factura = self.request.query_params.get('factura')
        if factura:
            queryset = queryset.filter(factura_id=factura)
        return queryset
