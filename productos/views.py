from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from empresas.views import EmpresaQuerysetMixin
from .models import Producto, ProductoProveedor, Proveedor, TipoProducto
from .serializers import (
    ProductoProveedorSerializer,
    ProductoSerializer,
    ProveedorSerializer,
    TipoProductoSerializer,
)


class TipoProductoViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    # The mixin applies the active company to this queryset.
    queryset = TipoProducto.objects.all()
    serializer_class = TipoProductoSerializer


class ProductoViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def _descargar_archivo(self, producto, field_name):
        archivo = getattr(producto, field_name)
        if not archivo:
            raise NotFound('El producto no tiene ese archivo disponible.')
        response = FileResponse(
            archivo.open('rb'),
            as_attachment=True,
            filename=Path(archivo.name).name,
        )
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    @action(detail=True, methods=['get'], url_path='manual', url_name='manual')
    def descargar_manual(self, request, pk=None):
        return self._descargar_archivo(self.get_object(), 'manual')

    @action(
        detail=True,
        methods=['get'],
        url_path='ficha-tecnica',
        url_name='ficha-tecnica',
    )
    def descargar_ficha_tecnica(self, request, pk=None):
        return self._descargar_archivo(self.get_object(), 'ficha_tecnica')

    @action(detail=False, methods=['get'], url_path='exportar-pdf')
    def exportar_pdf(self, request):
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )
        data = [['ID', 'Tipo', 'Descripción', 'Peso (kg)', 'Precio alquiler', 'Precio reposición']]

        for producto in self.get_queryset().select_related('tipo_producto').order_by('descripcion'):
            data.append([
                str(producto.id),
                producto.tipo_producto.nombre,
                producto.descripcion,
                str(producto.peso_kg),
                str(producto.precio_alquiler),
                str(producto.precio_reposicion),
            ])

        table = Table(
            [[Paragraph(escape(str(value)), styles['BodyText']) for value in row]
             for row in data],
            colWidths=[18 * mm, 42 * mm, 75 * mm, 25 * mm, 40 * mm, 45 * mm],
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        doc.build([
            Paragraph('LISTA DE PRODUCTOS', styles['Title']),
            Spacer(1, 8 * mm),
            table,
        ])
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='productos.pdf',
            content_type='application/pdf',
        )


class ProveedorViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer


class ProductoProveedorViewSet(EmpresaQuerysetMixin, viewsets.ModelViewSet):
    queryset = ProductoProveedor.objects.select_related('producto', 'proveedor')
    serializer_class = ProductoProveedorSerializer