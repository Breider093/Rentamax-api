from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Remision, RemisionAlarma, RemisionDetalle, RemisionReserva
from .services import (
    RemisionDomainError,
    cancelar_remision,
    confirmar_remision,
    entregar_remision,
    facturar_remision,
    reservar_remision,
)
from .serializers import (
    RemisionAlarmaSerializer,
    RemisionDetalleSerializer,
    RemisionReservaSerializer,
    RemisionSerializer,
)


class RemisionViewSet(viewsets.ModelViewSet):
    serializer_class = RemisionSerializer
    queryset = Remision.objects.select_related('cliente', 'transportador').prefetch_related('detalles__producto').all()

    def get_queryset(self):
        queryset = super().get_queryset()
        for field in ('cliente', 'transportador', 'estado', 'prioridad'):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{f'{field}_id' if field in ('cliente', 'transportador') else field: value})
        if self.request.query_params.get('sin_factura') == 'true':
            queryset = queryset.filter(factura__isnull=True)
        if self.request.query_params.get('vencidas') == 'true':
            queryset = queryset.filter(
                fecha_entrega_programada__lt=timezone.localdate(),
                estado__in=[Remision.Estado.PENDIENTE, Remision.Estado.RESERVADA],
            )
        return queryset

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        try:
            remision = confirmar_remision(pk, request.data.get('observaciones', ''))
        except RemisionDomainError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RemisionSerializer(remision).data)

    @action(detail=True, methods=['post'])
    def reservar(self, request, pk=None):
        try:
            remision, reserva = reservar_remision(pk, request.data.get('observaciones', ''))
        except RemisionDomainError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({**RemisionSerializer(remision).data, 'reserva_id': reserva.id})

    @action(detail=True, methods=['post'])
    def entregar(self, request, pk=None):
        try:
            remision = entregar_remision(pk)
        except RemisionDomainError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RemisionSerializer(remision).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            remision = cancelar_remision(pk)
        except RemisionDomainError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RemisionSerializer(remision).data)

    @action(detail=True, methods=['post'])
    def facturar(self, request, pk=None):
        try:
            remision, factura = facturar_remision(pk)
        except RemisionDomainError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'remision': RemisionSerializer(remision).data,
            'factura': {
                'id': factura.id, 'numero': factura.numero, 'estado': factura.estado,
                'subtotal': factura.subtotal, 'impuestos': factura.impuestos, 'total': factura.total,
            },
        })

    @action(detail=False, methods=['post'])
    def generar_alarmas(self, request):
        hoy = timezone.localdate()
        remisiones = self.get_queryset().filter(
            fecha_entrega_programada__lt=hoy,
            estado__in=[Remision.Estado.PENDIENTE, Remision.Estado.RESERVADA],
        )
        creadas = 0
        for remision in remisiones:
            _, created = RemisionAlarma.objects.get_or_create(
                remision=remision,
                tipo='ENTREGA_VENCIDA',
                estado=RemisionAlarma.Estado.PENDIENTE,
                defaults={
                    'prioridad': Remision.Prioridad.URGENTE,
                    'fecha_limite': remision.fecha_entrega_programada,
                    'descripcion': f'La remisión {remision.numero} tiene la entrega vencida.',
                },
            )
            creadas += int(created)
        sin_factura = self.get_queryset().filter(estado=Remision.Estado.ENTREGADA, factura__isnull=True)
        for remision in sin_factura:
            _, created = RemisionAlarma.objects.get_or_create(
                remision=remision,
                tipo='FACTURA_PENDIENTE',
                estado=RemisionAlarma.Estado.PENDIENTE,
                defaults={'descripcion': f'La remisión {remision.numero} no tiene factura asociada.'},
            )
            creadas += int(created)
        return Response({'alarmas_creadas': creadas})


class RemisionDetalleViewSet(viewsets.ModelViewSet):
    queryset = RemisionDetalle.objects.select_related('remision', 'producto').all()
    serializer_class = RemisionDetalleSerializer

    def perform_create(self, serializer):
        remision = serializer.validated_data.get('remision')
        if remision is None:
            raise serializers.ValidationError({'remision': 'Este campo es obligatorio.'})
        if remision.estado in (Remision.Estado.ENTREGADA, Remision.Estado.CANCELADA):
            raise serializers.ValidationError('No se pueden modificar remisiones entregadas o canceladas.')
        with transaction.atomic():
            serializer.save()
            remision.recalcular_totales()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.remision.estado in (Remision.Estado.ENTREGADA, Remision.Estado.CANCELADA):
            raise serializers.ValidationError('No se pueden modificar remisiones entregadas o canceladas.')
        with transaction.atomic():
            detail = serializer.save()
            detail.remision.recalcular_totales()

    def perform_destroy(self, instance):
        if instance.remision.estado in (Remision.Estado.ENTREGADA, Remision.Estado.CANCELADA):
            raise serializers.ValidationError('No se pueden modificar remisiones entregadas o canceladas.')
        remision = instance.remision
        with transaction.atomic():
            instance.delete()
            remision.recalcular_totales()


class RemisionReservaViewSet(viewsets.ModelViewSet):
    queryset = RemisionReserva.objects.select_related('remision').all()
    serializer_class = RemisionReservaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        remision = self.request.query_params.get('remision')
        estado = self.request.query_params.get('estado')
        if remision:
            queryset = queryset.filter(remision_id=remision)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == RemisionReserva.Estado.CANCELADA:
            return Response({'detail': 'La reserva ya está cancelada.'}, status=400)
        reserva.estado = RemisionReserva.Estado.CANCELADA
        reserva.cancelada_at = timezone.now()
        reserva.save(update_fields=['estado', 'cancelada_at'])
        return Response(self.get_serializer(reserva).data)


class RemisionAlarmaViewSet(viewsets.ModelViewSet):
    queryset = RemisionAlarma.objects.select_related('remision').all()
    serializer_class = RemisionAlarmaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        tipo = self.request.query_params.get('tipo')
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset

    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        alarma = self.get_object()
        alarma.estado = RemisionAlarma.Estado.RESUELTA
        alarma.resuelta_at = timezone.now()
        alarma.save(update_fields=['estado', 'resuelta_at'])
        return Response(self.get_serializer(alarma).data)
