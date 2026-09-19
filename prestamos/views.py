from rest_framework import viewsets
from rest_framework.decorators import action
from django.db.models import Q

from .models import EquipoObra, Prestamo, PrestamoDetalle
from .serializers import EquipoObraSerializer, PrestamoDetalleSerializer, PrestamoSerializer
from orden_compra.views import _exportar_excel, _exportar_pdf


class PrestamoViewSet(viewsets.ModelViewSet):
    serializer_class = PrestamoSerializer
    queryset = Prestamo.objects.select_related('cliente', 'obra').prefetch_related(
        'detalles__producto'
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        estado = self.request.query_params.get('estado')
        obra = self.request.query_params.get('obra')
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        if estado:
            queryset = queryset.filter(estado=estado)
        elif self.request.query_params.get('estado') is None:
            queryset = queryset.filter(estado=Prestamo.Estado.ACTIVO)
        if obra:
            queryset = queryset.filter(obra_id=obra)
        return queryset

    @action(detail=False, methods=['get'], url_path='exportar-equipos-obra-pdf')
    def exportar_equipos_obra_pdf(self, request):
        return _exportar_pdf(
            'EQUIPOS EN OBRA',
            'equipos-obra.pdf',
            _equipos_obra_headers(),
            _equipos_obra_rows(self.get_queryset()),
        )

    @action(detail=False, methods=['get'], url_path='exportar-equipos-obra-excel')
    def exportar_equipos_obra_excel(self, request):
        return _exportar_excel(
            'Equipos en obra',
            'equipos-obra.xlsx',
            _equipos_obra_headers(),
            _equipos_obra_rows(self.get_queryset()),
        )


class PrestamoDetalleViewSet(viewsets.ModelViewSet):
    queryset = PrestamoDetalle.objects.select_related('prestamo', 'producto').all()
    serializer_class = PrestamoDetalleSerializer


class EquipoObraViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoObraSerializer
    queryset = EquipoObra.objects.select_related(
        'producto', 'cliente', 'obra',
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente = self.request.query_params.get('cliente')
        obra = self.request.query_params.get('obra')
        descripcion = self.request.query_params.get('descripcion')
        estado = self.request.query_params.get('estado')
        if cliente and cliente.lower() != 'todos':
            if cliente.isdigit():
                queryset = queryset.filter(cliente_id=int(cliente))
            else:
                queryset = queryset.filter(cliente__razon_social__iexact=cliente)
        if obra and obra.lower() != 'todos':
            if obra.isdigit():
                queryset = queryset.filter(obra_id=int(obra))
            else:
                queryset = queryset.filter(obra__nombre__iexact=obra)
        if descripcion:
            queryset = queryset.filter(
                Q(descripcion__icontains=descripcion)
                | Q(producto__descripcion__icontains=descripcion)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        else:
            queryset = queryset.filter(estado=EquipoObra.Estado.ACTIVO)
        return queryset.order_by('obra__nombre', 'producto__descripcion', 'id')

    @action(detail=False, methods=['get'], url_path='exportar-pdf')
    def exportar_pdf(self, request):
        return _exportar_pdf(
            'EQUIPOS EN OBRA', 'equipos-obra.pdf', _equipos_obra_headers(),
            _equipo_obra_rows(self.get_queryset()),
        )

    @action(detail=False, methods=['get'], url_path='exportar-excel')
    def exportar_excel(self, request):
        return _exportar_excel(
            'Equipos en obra', 'equipos-obra.xlsx', _equipos_obra_headers(),
            _equipo_obra_rows(self.get_queryset()),
        )


def _equipos_obra_headers():
    return ['CLIENTE', 'OBRA', 'DESCRIPCIÓN', 'CANTIDAD', 'ESTADO']


def _equipo_obra_rows(queryset):
    return [[
        equipo.cliente.razon_social,
        equipo.obra.nombre,
        equipo.descripcion or equipo.producto.descripcion,
        equipo.cantidad,
        equipo.get_estado_display(),
    ] for equipo in queryset]


def _equipos_obra_rows(queryset):
    detalles = PrestamoDetalle.objects.filter(prestamo__in=queryset).select_related(
        'prestamo__cliente', 'prestamo__obra', 'producto',
    ).order_by('prestamo__obra__nombre', 'producto__descripcion')
    return [[
        detalle.prestamo.cliente.razon_social,
        detalle.prestamo.obra.nombre if detalle.prestamo.obra else '',
        detalle.producto.descripcion if detalle.producto else '',
        detalle.cantidad,
        detalle.prestamo.estado,
    ] for detalle in detalles]
