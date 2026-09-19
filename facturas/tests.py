from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from productos.models import Producto, TipoProducto

from .models import Factura


class FacturaFlowTests(APITestCase):
    def setUp(self):
        tipo = TipoProducto.objects.create(nombre='Material Factura')
        self.cliente = Cliente.objects.create(
            documento='CC-FAC-100', tipo_documento='CC', razon_social='Cliente Factura',
            direccion='Calle 1', ciudad='Bogota', email='factura@example.com', celular='3000000000',
        )
        self.producto = Producto.objects.create(descripcion='Producto Factura', tipo_producto=tipo)

    def test_crea_calcula_y_paga_factura(self):
        response = self.client.post(reverse('factura-list'), {
            'cliente': self.cliente.id,
            'fecha_emision': date.today().isoformat(),
            'impuestos': '10.00',
            'detalles': [{
                'producto': self.producto.id,
                'cantidad': '2.000',
                'precio_unitario': '25.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        factura = Factura.objects.get()
        self.assertEqual(factura.total, Decimal('60.00'))

        response = self.client.post(reverse('factura-pagar', args=[factura.id]), {
            'metodo_pago': 'TRANSFERENCIA',
            'monto': '60.00',
            'referencia': 'TRX-1',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Factura.objects.get().estado, Factura.Estado.PAGADA)
        self.assertEqual(Factura.objects.get().saldo_pendiente, Decimal('0.00'))

    def test_no_permite_pago_mayor_al_saldo(self):
        response = self.client.post(reverse('factura-list'), {
            'cliente': self.cliente.id,
            'fecha_emision': date.today().isoformat(),
            'detalles': [{
                'producto': self.producto.id,
                'cantidad': '1.000',
                'precio_unitario': '10.00',
            }],
        }, format='json')
        factura = Factura.objects.get()
        response = self.client.post(reverse('factura-pagar', args=[factura.id]), {
            'metodo_pago': 'EFECTIVO',
            'monto': '11.00',
        }, format='json')
        self.assertEqual(response.status_code, 400, response.data)
