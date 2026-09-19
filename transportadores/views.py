from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from remisiones.models import Remision

from .models import Transportador, TransportadorVehiculo, Vehiculo, Viaje, ViajeRemision
from .serializers import (
    TransportadorSerializer,
    TransportadorVehiculoSerializer,
    VehiculoSerializer,
    ViajeRemisionSerializer,
    ViajeSerializer,
)


class TransportadorViewSet(viewsets.ModelViewSet):
    queryset = Transportador.objects.prefetch_related('asignaciones_vehiculo__vehiculo').all()
    serializer_class = TransportadorSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        tipo = self.request.query_params.get('tipo')
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


class TransportadorVehiculoViewSet(viewsets.ModelViewSet):
    queryset = TransportadorVehiculo.objects.select_related('transportador', 'vehiculo').all()
    serializer_class = TransportadorVehiculoSerializer


class ViajeViewSet(viewsets.ModelViewSet):
    queryset = Viaje.objects.select_related('transportador', 'vehiculo').prefetch_related('remisiones').all()
    serializer_class = ViajeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        for field in ('transportador', 'vehiculo', 'estado'):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{f'{field}_id' if field != 'estado' else field: value})
        if self.request.query_params.get('destino'):
            queryset = queryset.filter(destino__icontains=self.request.query_params['destino'])
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        fecha_salida = self.request.query_params.get('fecha_salida')
        if fecha_salida:
            queryset = queryset.filter(fecha_salida__date=fecha_salida)
        if fecha_desde:
            queryset = queryset.filter(fecha_salida__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_salida__date__lte=fecha_hasta)
        return queryset

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        viaje = self.get_object()
        if viaje.estado != Viaje.Estado.PROGRAMADO:
            return Response({'detail': 'Solo se pueden iniciar viajes programados.'}, status=400)
        viaje.estado = Viaje.Estado.EN_CURSO
        viaje.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(viaje).data)

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        viaje = self.get_object()
        if viaje.estado != Viaje.Estado.EN_CURSO:
            return Response({'detail': 'Solo se pueden completar viajes en curso.'}, status=400)
        viaje.estado = Viaje.Estado.COMPLETADO
        viaje.fecha_llegada_real = timezone.now()
        viaje.save(update_fields=['estado', 'fecha_llegada_real', 'actualizado_en'])
        return Response(self.get_serializer(viaje).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        viaje = self.get_object()
        if viaje.estado in (Viaje.Estado.COMPLETADO, Viaje.Estado.CANCELADO):
            return Response({'detail': 'El viaje no se puede cancelar en su estado actual.'}, status=400)
        viaje.estado = Viaje.Estado.CANCELADO
        viaje.save(update_fields=['estado', 'actualizado_en'])
        return Response(self.get_serializer(viaje).data)


class ViajeRemisionViewSet(viewsets.ModelViewSet):
    queryset = ViajeRemision.objects.select_related('viaje', 'remision').all()
    serializer_class = ViajeRemisionSerializer

    def perform_create(self, serializer):
            viaje_id = serializer.validated_data['viaje'].pk
            remision_id = serializer.validated_data['remision'].pk
            with transaction.atomic():
                viaje = Viaje.objects.select_for_update().get(pk=viaje_id)
                remision = Remision.objects.select_for_update().get(pk=remision_id)
                if viaje.estado != Viaje.Estado.PROGRAMADO:
                    raise serializers.ValidationError({'viaje': 'Solo se pueden asignar viajes programados.'})
                if remision.estado in (Remision.Estado.ENTREGADA, Remision.Estado.CANCELADA):
                    raise serializers.ValidationError({'remision': 'La remisión no está disponible para asignación.'})
                if remision.asignaciones_viaje.exists():
                    raise serializers.ValidationError({'remision': 'La remisión ya está asignada a otro viaje.'})
                serializer.save(viaje=viaje, remision=remision)
