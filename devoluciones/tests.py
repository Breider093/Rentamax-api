from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from obras.models import Obra
from productos.models import Producto, TipoProducto
from transportadores.models import Transportador

from .models import Devolucion


class DevolucionFlowTests(APITestCase):
    def setUp(self):
        tipo = TipoProducto.objects.create(nombre='Material')
        self.cliente = Cliente.objects.create(
            documento='CC-DEV-100', tipo_documento='CC', razon_social='Cliente Devolucion',
            direccion='Calle 1', ciudad='Bogota', email='dev@example.com', celular='3000000000',
        )
        self.obra = Obra.objects.create(
            cliente=self.cliente, nombre='Obra Uno', direccion='Carrera 1'
        )
        self.transportador = Transportador.objects.create(
            nombre='Transportador Uno', documento='NIT-DEV-100'
        )
        self.producto = Producto.objects.create(descripcion='Producto Devuelto', tipo_producto=tipo, peso_kg='2.50')

    def test_crea_calcula_procesa_y_filtra_devolucion_sin_factura(self):
        response = self.client.post(reverse('devolucion-list'), {
            'cliente': self.cliente.id,
            'obra': self.obra.id,
            'transportador': self.transportador.id,
            'fecha_factura': date.today().isoformat(),
            'precio_transporte': '15.00',
            'detalles': [{
                'producto': self.producto.id,
                'cantidad': '3.000',
                'peso_unitario': '2.500',
                'motivo': 'DEFECTUOSO',
            }],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        devolucion = Devolucion.objects.get()
        self.assertEqual(devolucion.detalles.get().total_kg, Decimal('7.500'))
        self.assertEqual(devolucion.estado_factura, Devolucion.EstadoFactura.SIN_FACTURA)

        response = self.client.post(reverse('devolucion-procesar', args=[devolucion.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Devolucion.objects.get().estado, Devolucion.Estado.PROCESADA)

        response = self.client.get(reverse('devolucion-list'), {'sin_factura': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_rechaza_obra_de_otro_cliente(self):
        otro_cliente = Cliente.objects.create(
            documento='CC-DEV-200', tipo_documento='CC', razon_social='Otro Cliente',
            direccion='Calle 2', ciudad='Bogota', email='otro@example.com', celular='3111111111',
        )
        otra_obra = Obra.objects.create(
            cliente=otro_cliente, nombre='Otra Obra', direccion='Carrera 2'
        )
        response = self.client.post(reverse('devolucion-list'), {
            'cliente': self.cliente.id,
            'obra': otra_obra.id,
            'transportador': self.transportador.id,
        }, format='json')
        self.assertEqual(response.status_code, 400)
