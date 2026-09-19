from io import BytesIO
from xml.sax.saxutils import escape

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import viewsets
from rest_framework.decorators import action

from .models import Cliente, ClienteDocumento
from .serializers import ClienteDocumentoSerializer, ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.prefetch_related('documentos').all()
    serializer_class = ClienteSerializer

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
        data = [[
            'Documento',
            'Razón social',
            'Dirección',
            'Ciudad',
            'Correo',
            'Teléfono',
            'Celular',
            'Estado',
        ]]

        for cliente in self.get_queryset().order_by('razon_social'):
            data.append([
                cliente.documento,
                cliente.razon_social,
                cliente.direccion,
                cliente.ciudad,
                cliente.email,
                cliente.telefono,
                cliente.celular,
                'Habilitado' if cliente.habilitado else 'Inhabilitado',
            ])

        table = Table(
            [[Paragraph(escape(str(value)), styles['BodyText']) for value in row]
             for row in data],
            colWidths=[28 * mm, 42 * mm, 40 * mm, 25 * mm, 45 * mm, 25 * mm, 25 * mm, 27 * mm],
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
            Paragraph('LISTA DE CLIENTES', styles['Title']),
            Spacer(1, 8 * mm),
            table,
        ])
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='clientes.pdf',
            content_type='application/pdf',
        )


class ClienteDocumentoViewSet(viewsets.ModelViewSet):
    queryset = ClienteDocumento.objects.select_related('cliente').all()
    serializer_class = ClienteDocumentoSerializer
