from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from clientes.models import Cliente
from kardex.models import KardexMovimiento
from productos.models import Producto, TipoProducto

from .models import Remision, RemisionAlarma


class RemisionApiTests(APITestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            documento='900123456-7',
            tipo_documento='NIT',
            razon_social='Constructora Ejemplo S.A.S.',
            direccion='Carrera 10 # 20-30',
            ciudad='Bogota',
            email='contacto@ejemplo.com',
            celular='3001234567',
        )
        tipo, _ = TipoProducto.objects.get_or_create(nombre='Andamios')
        self.producto = Producto.objects.create(
            descripcion='Andamio estandar',
            tipo_producto=tipo,
            precio_alquiler=Decimal('100.00'),
        )

    def crear_remision(self):
        response = self.client.post(
            reverse('remision-list'),
            {
                'cliente': self.cliente.pk,
                'fecha_entrega_programada': str(date.today() + timedelta(days=1)),
                'impuestos': '0.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        return response.data

    def test_crea_detalle_y_entrega_crea_kardex(self):
        remision = self.crear_remision()
        detalle = self.client.post(
            reverse('remision-detalle-list'),
            {
                'remision': remision['id'],
                'producto': self.producto.pk,
                'cantidad': '2.000',
                'precio_unitario': '100.00',
            },
            format='json',
        )
        self.assertEqual(detalle.status_code, 201)
        self.assertEqual(detalle.data['subtotal'], '200.00')

        confirmacion = self.client.post(
            reverse('remision-confirmar', args=[remision['id']]),
            {},
            format='json',
        )
        self.assertEqual(confirmacion.status_code, 200)
        self.assertEqual(confirmacion.data['estado'], Remision.Estado.CONFIRMADA)

        entrega = self.client.post(
            reverse('remision-entregar', args=[remision['id']]),
            {},
            format='json',
        )
        self.assertEqual(entrega.status_code, 200)
        self.assertEqual(entrega.data['estado'], Remision.Estado.ENTREGADA)
        self.assertEqual(KardexMovimiento.objects.filter(remision_id=remision['id']).count(), 1)

    def test_filtra_remisiones_sin_factura(self):
        remision = self.crear_remision()
        response = self.client.get(reverse('remision-list'), {'sin_factura': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [remision['id']])

    def test_genera_alarma_de_entrega_vencida(self):
        remision = Remision.objects.create(
            cliente=self.cliente,
            fecha_entrega_programada=timezone.localdate() - timedelta(days=1),
        )
        response = self.client.post(reverse('remision-generar-alarmas'), {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alarmas_creadas'], 1)
        self.assertTrue(RemisionAlarma.objects.filter(remision=remision).exists())
