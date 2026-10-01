from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Empresa, Membresia


def crear_usuario_empresa(username, empresa, rol=Membresia.Rol.ADMIN, **user_fields):
    User = get_user_model()
    usuario = User.objects.create_user(
        username=username,
        password='TestPassword-123!',
        is_staff=False,
        is_superuser=False,
        **user_fields,
    )
    Membresia.objects.create(usuario=usuario, empresa=empresa, rol=rol)
    return usuario


class EmpresaAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.empresa = Empresa.objects.create(
            nombre='Empresa de pruebas',
            nit='TEST-EMPRESA',
        )
        self.usuario = crear_usuario_empresa('usuario-prueba', self.empresa)
        self.client.force_authenticate(self.usuario)
