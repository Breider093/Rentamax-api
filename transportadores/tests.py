from datetime import date, datetime, timedelta

from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from remisiones.models import Remision

from .models import Viaje


class TransportadoresApiTests(APITestCase):
    def test_crea_asigna_y_completa_viaje(self):
        transportador_response = self.client.post(
            reverse('transportador-list'),
            {
                'nombre': 'Carlos Perez',
                'documento': '123456789',
                'telefono': '3001234567',
                'licencia_numero': 'LIC-123',
                'licencia_categoria': 'C2',
            },
            format='json',
        )
        self.assertEqual(transportador_response.status_code, 201)
        transportador = transportador_response.data
        self.assertEqual(transportador['codigo'], 'TR001')

        vehiculo_response = self.client.post(
            reverse('vehiculo-list'),
            {'placa': 'ABC123', 'tipo': 'CAMION', 'capacidad_kg': '5000.00'},
            format='json',
        )
        self.assertEqual(vehiculo_response.status_code, 201)
        vehiculo = vehiculo_response.data

        asignacion_response = self.client.post(
            reverse('transportador-vehiculo-list'),
            {
                'transportador': transportador['id'],
                'vehiculo': vehiculo['id'],
                'es_principal': True,
            },
            format='json',
        )
        self.assertEqual(asignacion_response.status_code, 201)

        viaje_response = self.client.post(
            reverse('viaje-list'),
            {
                'transportador': transportador['id'],
                'vehiculo': vehiculo['id'],
                'destino': 'Medellin',
                'fecha_salida': datetime.now().isoformat(),
            },
            format='json',
        )
        self.assertEqual(viaje_response.status_code, 201)
        viaje_id = viaje_response.data['id']

        cliente = Cliente.objects.create(
            documento='900123456-7',
            tipo_documento='NIT',
            razon_social='Constructora Ejemplo',
            direccion='Carrera 1',
            ciudad='Bogota',
            email='contacto@ejemplo.com',
            celular='3000000000',
        )
        remision = Remision.objects.create(
            cliente=cliente,
            fecha_entrega_programada=date.today() + timedelta(days=1),
        )
        asociacion = self.client.post(
            reverse('viaje-remision-list'),
            {'viaje': viaje_id, 'remision': remision.id},
            format='json',
        )
        self.assertEqual(asociacion.status_code, 201)

        iniciar = self.client.post(reverse('viaje-iniciar', args=[viaje_id]), {}, format='json')
        self.assertEqual(iniciar.status_code, 200)
        self.assertEqual(iniciar.data['estado'], Viaje.Estado.EN_CURSO)

        completar = self.client.post(reverse('viaje-completar', args=[viaje_id]), {}, format='json')
        self.assertEqual(completar.status_code, 200)
        self.assertEqual(completar.data['estado'], Viaje.Estado.COMPLETADO)

    def test_rechaza_vehiculo_no_asignado_al_transportador(self):
        transportador = self.client.post(
            reverse('transportador-list'),
            {'nombre': 'Carlos Perez', 'documento': '123456789'},
            format='json',
        ).data
        vehiculo = self.client.post(
            reverse('vehiculo-list'),
            {'placa': 'ABC123', 'tipo': 'CAMION'},
            format='json',
        ).data

        response = self.client.post(
            reverse('viaje-list'),
            {
                'transportador': transportador['id'],
                'vehiculo': vehiculo['id'],
                'destino': 'Medellin',
                'fecha_salida': datetime.now().isoformat(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('vehiculo', response.data)

    def test_rechaza_asignacion_de_vehiculo_inactivo(self):
        transportador = self.client.post(
            reverse('transportador-list'),
            {'nombre': 'Carlos Perez', 'documento': '123456789'},
            format='json',
        ).data
        vehiculo = self.client.post(
            reverse('vehiculo-list'),
            {'placa': 'ABC123', 'tipo': 'CAMION', 'estado': 'MANTENIMIENTO'},
            format='json',
        ).data

        response = self.client.post(
            reverse('transportador-vehiculo-list'),
            {'transportador': transportador['id'], 'vehiculo': vehiculo['id']},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('vehiculo', response.data)
