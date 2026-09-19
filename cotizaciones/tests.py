from django.test import TestCase

from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from productos.models import Producto, TipoProducto
from facturas.models import Factura

from .models import Cotizacion


class CotizacionFlowTests(APITestCase):
	def setUp(self):
		tipo = TipoProducto.objects.create(nombre='Material')
		self.cliente = Cliente.objects.create(
			documento='CC-100',
			tipo_documento='CC',
			razon_social='Cliente Uno',
			direccion='Calle 1',
			ciudad='Bogota',
			email='cliente@example.com',
			celular='3000000000',
		)
		self.producto = Producto.objects.create(
			descripcion='Producto Uno',
			tipo_producto=tipo,
		)

	def test_crea_calcula_y_aprueba_cotizacion(self):
		response = self.client.post(reverse('cotizacion-list'), {
			'cliente': self.cliente.id,
			'fecha_vencimiento': (date.today() + timedelta(days=15)).isoformat(),
			'impuestos': '10.00',
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '2.000',
				'precio_unitario': '25.00',
			}],
		}, format='json')
		self.assertEqual(response.status_code, 201, response.data)
		cotizacion = Cotizacion.objects.get()
		self.assertEqual(cotizacion.subtotal, Decimal('50.00'))
		self.assertEqual(cotizacion.total, Decimal('60.00'))

		response = self.client.post(reverse('cotizacion-aprobar', args=[cotizacion.id]))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Cotizacion.objects.get().estado, Cotizacion.Estado.APROBADA)

	def test_no_permite_cliente_deshabilitado(self):
		self.cliente.habilitado = False
		self.cliente.save(update_fields=['habilitado'])
		response = self.client.post(reverse('cotizacion-list'), {
			'cliente': self.cliente.id,
			'fecha_vencimiento': (date.today() + timedelta(days=15)).isoformat(),
		}, format='json')
		self.assertEqual(response.status_code, 400)

	def test_convierte_cotizacion_en_factura(self):
		response = self.client.post(reverse('cotizacion-list'), {
			'cliente': self.cliente.id,
			'vigencia_dias': 15,
			'impuestos': '10.00',
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '2.000',
				'precio_unitario': '25.00',
			}],
		}, format='json')
		self.assertEqual(response.status_code, 201, response.data)

		cotizacion = Cotizacion.objects.get()
		response = self.client.post(
			reverse('cotizacion-convertir-factura', args=[cotizacion.id])
		)

		self.assertEqual(response.status_code, 201, response.data)
		factura = Factura.objects.get(cotizacion=cotizacion)
		self.assertEqual(factura.total, Decimal('60.00'))
		self.assertEqual(factura.detalles.count(), 1)
		self.assertEqual(cotizacion.refresh_from_db(), None)
		self.assertEqual(cotizacion.estado, Cotizacion.Estado.CONVERTIDA)
