from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from productos.models import Producto, Proveedor, TipoProducto

from .models import Entrada, Inventario, MovimientoInventario, OrdenCompra, Salida


class OrdenCompraFlowTests(APITestCase):
	def setUp(self):
		tipo = TipoProducto.objects.create(nombre='Material')
		self.proveedor = Proveedor.objects.create(nombre='Proveedor Uno', nit='900123456-1')
		self.producto = Producto.objects.create(descripcion='Producto Uno', tipo_producto=tipo)

	def test_crea_aprueba_y_confirma_entrada_actualizando_inventario(self):
		orden_response = self.client.post(reverse('orden-compra-list'), {
			'proveedor': self.proveedor.id,
			'fecha_entrega_programada': date.today().isoformat(),
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '5.000',
				'precio_unitario': '12.50',
			}],
		}, format='json')
		self.assertEqual(orden_response.status_code, 201, orden_response.data)
		orden = OrdenCompra.objects.get()
		self.assertEqual(orden.total, Decimal('62.50'))

		aprobar_response = self.client.post(reverse('orden-compra-aprobar', args=[orden.id]))
		self.assertEqual(aprobar_response.status_code, 200)

		entrada_response = self.client.post(reverse('entrada-list'), {
			'proveedor': self.proveedor.id,
			'orden_compra': orden.id,
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '5.000',
				'precio_unitario': '12.50',
			}],
		}, format='json')
		self.assertEqual(entrada_response.status_code, 201)
		entrada = Entrada.objects.get()

		confirmar_response = self.client.post(reverse('entrada-confirmar', args=[entrada.id]))
		self.assertEqual(confirmar_response.status_code, 200)
		self.assertEqual(Inventario.objects.get(producto=self.producto).existencia, Decimal('5.000'))
		self.assertEqual(OrdenCompra.objects.get().estado, OrdenCompra.Estado.COMPLETADA)
		self.assertEqual(MovimientoInventario.objects.filter(tipo='ENTRADA').count(), 1)

	def test_completa_salida_y_descuenta_inventario(self):
		Inventario.objects.create(producto=self.producto, existencia=Decimal('5.000'))
		response = self.client.post(reverse('salida-list'), {
			'fecha': date.today().isoformat(),
			'tipo': 'VENTA',
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '2.000',
				'precio_unitario': '12.50',
			}],
		}, format='json')
		self.assertEqual(response.status_code, 201, response.data)
		salida = Salida.objects.get()

		response = self.client.post(reverse('salida-completar', args=[salida.id]))
		self.assertEqual(response.status_code, 200, response.data)
		self.assertEqual(Inventario.objects.get(producto=self.producto).existencia, Decimal('3.000'))
		self.assertEqual(Salida.objects.get().estado, Salida.Estado.COMPLETADA)
		self.assertEqual(MovimientoInventario.objects.filter(tipo='SALIDA').count(), 1)

	def test_no_completa_salida_sin_stock(self):
		response = self.client.post(reverse('salida-list'), {
			'tipo': 'VENTA',
			'detalles': [{
				'producto': self.producto.id,
				'cantidad': '1.000',
				'precio_unitario': '12.50',
			}],
		}, format='json')
		salida = Salida.objects.get()

		response = self.client.post(reverse('salida-completar', args=[salida.id]))
		self.assertEqual(response.status_code, 400, response.data)
		self.assertEqual(Salida.objects.get().estado, Salida.Estado.PENDIENTE)
