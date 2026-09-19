from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Devolucion, DevolucionDetalle
from .serializers import DevolucionDetalleSerializer, DevolucionSerializer


class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.select_related(
        'cliente', 'obra', 'transportador', 'factura', 'creado_por'
    ).prefetch_related('detalles__producto').all()
    serializer_class = DevolucionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        for field in ('cliente', 'obra', 'transportador', 'factura', 'estado', 'estado_factura'):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{f'{field}_id' if field in ('cliente', 'obra', 'transportador', 'factura') else field: value})
        if self.request.query_params.get('sin_factura') == 'true':
            queryset = queryset.filter(factura__isnull=True)
        if self.request.query_params.get('vencidas') == 'true':
            queryset = queryset.filter(
                fecha_entrega__lt=timezone.now(), estado=Devolucion.Estado.PENDIENTE
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        if serializer.instance.estado != Devolucion.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden editar devoluciones pendientes.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        devolucion = self.get_object()
        if devolucion.estado != Devolucion.Estado.PENDIENTE:
            return Response({'detail': 'Solo se pueden procesar devoluciones pendientes.'}, status=400)
        if not devolucion.detalles.exists():
            return Response({'detail': 'La devolución debe tener al menos un producto.'}, status=400)
        devolucion.estado = Devolucion.Estado.PROCESADA
        devolucion.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(devolucion).data)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        devolucion = self.get_object()
        if devolucion.estado != Devolucion.Estado.PENDIENTE:
            return Response({'detail': 'Solo se pueden rechazar devoluciones pendientes.'}, status=400)
        devolucion.estado = Devolucion.Estado.RECHAZADA
        devolucion.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(devolucion).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        devolucion = self.get_object()
        if devolucion.estado in (Devolucion.Estado.PROCESADA, Devolucion.Estado.CANCELADA):
            return Response({'detail': 'La devolución no se puede cancelar en su estado actual.'}, status=400)
        devolucion.estado = Devolucion.Estado.CANCELADA
        devolucion.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(devolucion).data)


class DevolucionDetalleViewSet(viewsets.ModelViewSet):
    queryset = DevolucionDetalle.objects.select_related('devolucion', 'producto').all()
    serializer_class = DevolucionDetalleSerializer

    def perform_create(self, serializer):
        devolucion = serializer.validated_data['devolucion']
        if devolucion.estado != Devolucion.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar devoluciones pendientes.')
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance.devolucion.estado != Devolucion.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar devoluciones pendientes.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.devolucion.estado != Devolucion.Estado.PENDIENTE:
            raise serializers.ValidationError('Solo se pueden modificar devoluciones pendientes.')
        instance.delete()
