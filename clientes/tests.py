from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Cliente, ClienteDocumento


class ClienteApiTests(APITestCase):
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

    def test_lista_clientes(self):
        response = self.client.get(reverse('cliente-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['documento'], self.cliente.documento)

    def test_crea_documento_para_cliente(self):
        archivo = SimpleUploadedFile('rut.pdf', b'contenido', content_type='application/pdf')

        response = self.client.post(
            reverse('cliente-documento-list'),
            {
                'cliente': self.cliente.pk,
                'tipo': ClienteDocumento.Tipo.RUT,
                'archivo': archivo,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(ClienteDocumento.objects.filter(cliente=self.cliente).exists())
