from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from obras.models import Obra
from productos.models import Producto, TipoProducto

from .models import KardexDetalle, KardexMovimiento


class KardexApiTests(APITestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            documento='900123456-7',
            tipo_documento='NIT',
            razon_social='Constructora Ejemplo S.A.S.',
            direccion='Carrera 10 # 20-30',
            ciudad='Bogotá',
            email='contacto@ejemplo.com',
            celular='3001234567',
        )
        self.obra = Obra.objects.create(
            cliente=self.cliente,
            nombre='Obra principal',
            direccion='Calle 1 # 2-3',
        )
        self.tipo_producto, _ = TipoProducto.objects.get_or_create(
            nombre='Andamios'
        )
        self.producto = Producto.objects.create(
            descripcion='Andamio estándar',
            tipo_producto=self.tipo_producto,
        )

    def crear_movimiento(self, tipo, valor):
        return KardexMovimiento.objects.create(
            cliente=self.cliente,
            tipo=tipo,
            valor=valor,
        )

    def test_detalle_calcula_subtotal(self):
        movimiento = self.crear_movimiento(KardexMovimiento.Tipo.PRESTAMO, 100)

        detalle = KardexDetalle.objects.create(
            movimiento=movimiento,
            producto=self.producto,
            cantidad=Decimal('2.50'),
            precio_unitario=Decimal('40.00'),
        )

        self.assertEqual(detalle.subtotal, Decimal('100.00'))

    def test_saldo_aplica_signo_por_tipo(self):
        self.crear_movimiento(KardexMovimiento.Tipo.VENTA, Decimal('100.00'))
        self.crear_movimiento(KardexMovimiento.Tipo.PRESTAMO, Decimal('50.00'))
        self.crear_movimiento(KardexMovimiento.Tipo.REPOSICION, Decimal('25.00'))
        self.crear_movimiento(KardexMovimiento.Tipo.PAGO, Decimal('80.00'))
        self.crear_movimiento(KardexMovimiento.Tipo.DEVOLUCION, Decimal('10.00'))

        response = self.client.get(
            reverse('kardex-movimiento-saldo'),
            {'cliente': self.cliente.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['saldo'], Decimal('85.00'))

    def test_filtra_movimientos_por_cliente(self):
        self.crear_movimiento(KardexMovimiento.Tipo.VENTA, Decimal('100.00'))

        response = self.client.get(
            reverse('kardex-movimiento-list'),
            {'cliente': self.cliente.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_crea_movimiento_asociado_a_obra(self):
        response = self.client.post(
            reverse('kardex-movimiento-list'),
            {
                'cliente': self.cliente.pk,
                'obra': self.obra.pk,
                'tipo': KardexMovimiento.Tipo.PRESTAMO,
                'valor': '250000.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['obra'], self.obra.pk)

    def test_rechaza_obra_de_otro_cliente(self):
        otro_cliente = Cliente.objects.create(
            documento='900765432-1',
            tipo_documento='NIT',
            razon_social='Otra empresa',
            direccion='Carrera 5 # 6-7',
            ciudad='Medellín',
            email='otra@ejemplo.com',
            celular='3007654321',
        )
        otra_obra = Obra.objects.create(
            cliente=otro_cliente,
            nombre='Obra ajena',
            direccion='Carrera 5 # 6-7',
        )

        response = self.client.post(
            reverse('kardex-movimiento-list'),
            {
                'cliente': self.cliente.pk,
                'obra': otra_obra.pk,
                'tipo': KardexMovimiento.Tipo.PRESTAMO,
                'valor': '100.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
