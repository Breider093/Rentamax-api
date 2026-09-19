from decimal import Decimal

from django.db.models import Case, DecimalField, F, Sum, When
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from clientes.models import Cliente

from .models import KardexDetalle, KardexMovimiento
from .serializers import KardexDetalleSerializer, KardexMovimientoSerializer


def _movimiento_valor(movimiento):
    if movimiento.tipo in (KardexMovimiento.Tipo.PAGO, KardexMovimiento.Tipo.DEVOLUCION):
        return -movimiento.valor
    return movimiento.valor


class KardexClienteView(APIView):
    def get(self, request, cliente_id):
        desde = parse_date(request.query_params.get('desde', ''))
        hasta = parse_date(request.query_params.get('hasta', ''))
        if request.query_params.get('desde') and desde is None:
            return Response({'detail': 'La fecha desde no es válida.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.query_params.get('hasta') and hasta is None:
            return Response({'detail': 'La fecha hasta no es válida.'}, status=status.HTTP_400_BAD_REQUEST)
        if desde and hasta and desde > hasta:
            return Response({'detail': 'El rango de fechas no es válido.'}, status=status.HTTP_400_BAD_REQUEST)

        get_object_or_404(Cliente.objects.only('id'), pk=cliente_id)
        queryset = KardexMovimiento.objects.filter(cliente_id=cliente_id).select_related('obra').prefetch_related(
            'detalles__producto'
        ).order_by('fecha', 'id')
        obra = request.query_params.get('obra')
        if obra:
            queryset = queryset.filter(obra_id=obra)
        corte = queryset
        if desde:
            corte = corte.filter(fecha__date__gte=desde)
        if hasta:
            corte = corte.filter(fecha__date__lte=hasta)
        saldo_inicial = sum((_movimiento_valor(movimiento) for movimiento in queryset if not desde or movimiento.fecha.date() < desde), Decimal('0.00'))
        saldo = saldo_inicial
        movimientos = []
        for movimiento in corte:
            saldo_anterior = saldo
            saldo += _movimiento_valor(movimiento)
            movimientos.append({
                'id': movimiento.id,
                'fecha': movimiento.fecha,
                'tipo': movimiento.tipo,
                'documento': movimiento.numero_documento,
                'obra': movimiento.obra_id,
                'cantidad': sum((detalle.cantidad for detalle in movimiento.detalles.all()), Decimal('0.000')),
                'precio_unitario': movimiento.detalles.first().precio_unitario if movimiento.detalles.exists() else Decimal('0.00'),
                'subtotal': movimiento.valor,
                'debito': movimiento.valor if _movimiento_valor(movimiento) >= 0 else Decimal('0.00'),
                'credito': movimiento.valor if _movimiento_valor(movimiento) < 0 else Decimal('0.00'),
                'saldo_anterior': saldo_anterior,
                'saldo': saldo,
                'detalles': KardexDetalleSerializer(movimiento.detalles.all(), many=True).data,
            })
        return Response({
            'cliente': cliente_id,
            'desde': desde,
            'hasta': hasta,
            'saldo_inicial': saldo_inicial,
            'saldo_final': saldo,
            'movimientos': movimientos,
        })


class KardexMovimientoViewSet(viewsets.ModelViewSet):
    serializer_class = KardexMovimientoSerializer
    queryset = KardexMovimiento.objects.select_related('cliente', 'obra', 'remision').prefetch_related(
        'detalles__producto'
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        obra = self.request.query_params.get('obra')

        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        if fecha_desde:
            queryset = queryset.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__date__lte=fecha_hasta)
        if obra:
            queryset = queryset.filter(obra_id=obra)
        return queryset

    @action(detail=False, methods=['get'])
    def saldo(self, request):
        cliente = request.query_params.get('cliente')
        if not cliente:
            return Response(
                {'detail': 'El parámetro cliente es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saldo = self.get_queryset().filter(cliente_id=cliente).aggregate(
            saldo=Coalesce(
                Sum(
                    Case(
                        When(
                            tipo__in=[
                                KardexMovimiento.Tipo.VENTA,
                                KardexMovimiento.Tipo.PRESTAMO,
                                KardexMovimiento.Tipo.REPOSICION,
                            ],
                            then='valor',
                        ),
                        When(
                            tipo__in=[
                                KardexMovimiento.Tipo.PAGO,
                                KardexMovimiento.Tipo.DEVOLUCION,
                            ],
                            then=-1 * F('valor'),
                        ),
                        default=0,
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ),
                0,
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )['saldo']
        return Response({'cliente': int(cliente), 'saldo': saldo})


class KardexDetalleViewSet(viewsets.ModelViewSet):
    queryset = KardexDetalle.objects.select_related('movimiento', 'producto').all()
    serializer_class = KardexDetalleSerializer
