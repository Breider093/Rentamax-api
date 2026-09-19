from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from obras.models import Obra
from productos.models import Producto, TipoProducto

from .models import Prestamo, PrestamoDetalle


class PrestamoApiTests(APITestCase):
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
        tipo, _ = TipoProducto.objects.get_or_create(nombre='Andamios')
        self.producto = Producto.objects.create(
            descripcion='Andamio para préstamo',
            tipo_producto=tipo,
        )
        self.prestamo = Prestamo.objects.create(
            cliente=self.cliente,
            obra=self.obra,
            fecha_reserva=date(2026, 9, 7),
        )

    def test_crea_detalle_y_actualiza_total(self):
        response = self.client.post(
            reverse('prestamo-detalle-list'),
            {
                'prestamo': self.prestamo.pk,
                'producto': self.producto.pk,
                'cantidad': '2.00',
                'precio_unitario': '50000.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.prestamo.refresh_from_db()
        self.assertEqual(self.prestamo.total, Decimal('100000.00'))

    def test_filtra_prestamos_por_cliente_y_estado(self):
        self.prestamo.estado = Prestamo.Estado.PENDIENTE
        self.prestamo.save(update_fields=['estado'])

        response = self.client.get(
            reverse('prestamo-list'),
            {'cliente': self.cliente.pk, 'estado': Prestamo.Estado.PENDIENTE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

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

        response = self.client.patch(
            reverse('prestamo-detail', args=[self.prestamo.pk]),
            {'obra': otra_obra.pk},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
