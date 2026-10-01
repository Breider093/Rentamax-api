from datetime import date
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from reportlab.platypus import Table as ReportTable
from rest_framework.exceptions import ValidationError

from clientes.models import Cliente
from clientes.serializers import ClienteSerializer
from clientes.models import ClienteDocumento
from empresas.models import Empresa, Membresia
from empresas.testing import EmpresaAPITestCase, crear_usuario_empresa
from facturas.models import Factura
from orden_compra.models import Entrada, Salida
from productos.models import TipoProducto
from productos.serializers import ProductoSerializer, TipoProductoSerializer
from productos.models import Producto, Proveedor
from remisiones.models import Remision
from remisiones.services import confirmar_remision
from transportadores.models import Transportador, Viaje


class EmpresaSerializerMixinTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa A', nit='900000001')
        self.otra_empresa = Empresa.objects.create(nombre='Empresa B', nit='900000002')
        self.context = {'request': SimpleNamespace(empresa=self.empresa)}

    def test_el_cliente_no_puede_enviar_empresa(self):
        serializer = ClienteSerializer(
            data={
                'documento': '900123456',
                'razon_social': 'Cliente A',
                'direccion': 'Calle 1',
                'ciudad': 'Bogotá',
                'email': 'cliente@example.com',
                'celular': '3000000000',
                'empresa': self.otra_empresa.pk,
            },
            context=self.context,
        )

        self.assertNotIn('empresa', serializer.fields)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        cliente = serializer.save()
        self.assertEqual(cliente.empresa, self.empresa)

    def test_no_acepta_fk_a_otra_empresa(self):
        tipo_ajeno = TipoProducto.objects.create(empresa=self.otra_empresa, nombre='Tipo B')
        serializer = ProductoSerializer(
            data={
                'descripcion': 'Producto de prueba',
                'tipo_producto': tipo_ajeno.pk,
                'peso_kg': '1.00',
                'precio_alquiler': '10.00',
                'precio_reposicion': '20.00',
            },
            context=self.context,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('tipo_producto', serializer.errors)

    def test_serializer_sin_empresa_no_expone_fks_de_tenant(self):
        tipo = TipoProducto.objects.create(empresa=self.empresa, nombre='Tipo A')
        serializer = ProductoSerializer(
            data={
                'descripcion': 'Producto sin contexto',
                'tipo_producto': tipo.pk,
                'peso_kg': '1.00',
                'precio_alquiler': '10.00',
                'precio_reposicion': '20.00',
            },
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serializer_de_tipo_asigna_empresa_del_request(self):
        serializer = TipoProductoSerializer(
            data={'nombre': 'Tipo A'},
            context=self.context,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        tipo = serializer.save()
        self.assertEqual(tipo.empresa, self.empresa)

    def test_servicio_no_recupera_remision_de_otra_empresa(self):
        cliente = Cliente.objects.create(
            empresa=self.empresa,
            documento='900123456',
            razon_social='Cliente A',
            direccion='Calle 1',
            ciudad='Bogotá',
            email='cliente@example.com',
            celular='3000000000',
        )
        remision = Remision.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            fecha_entrega_programada=date(2026, 10, 1),
        )

        with self.assertRaises(Http404):
            confirmar_remision(remision.pk, self.otra_empresa)


class AislamientoApiTests(EmpresaAPITestCase):
    def setUp(self):
        super().setUp()
        self.otra_empresa = Empresa.objects.create(nombre='Empresa B', nit='TEST-EMPRESA-B')
        self.usuario_b = crear_usuario_empresa('usuario-b', self.otra_empresa)
        self.cliente_a = Cliente.objects.create(
            empresa=self.empresa,
            documento='DOC-A',
            razon_social='Cliente A',
            direccion='Calle A',
            ciudad='Bogotá',
            email='a@example.com',
            celular='3000000000',
        )
        self.cliente_b = Cliente.objects.create(
            empresa=self.otra_empresa,
            documento='DOC-B',
            razon_social='Cliente B confidencial',
            direccion='Calle B',
            ciudad='Medellín',
            email='b@example.com',
            celular='3111111111',
        )

    def test_no_lista_ni_recupera_ni_modifica_ni_elimina_cliente_ajeno(self):
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.cliente_a.pk])

        detail_url = reverse('cliente-detail', args=[self.cliente_b.pk])
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.patch(detail_url, {'razon_social': 'Vulnerado'}).status_code,
            404,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, 404)
        self.cliente_b.refresh_from_db()
        self.assertEqual(self.cliente_b.razon_social, 'Cliente B confidencial')

    def test_exportar_pdf_solo_incluye_clientes_de_la_empresa(self):
        with patch('clientes.views.Table', wraps=ReportTable) as table_spy:
            response = self.client.get(reverse('cliente-exportar-pdf'))
        self.assertEqual(response.status_code, 200)
        contenido = b''.join(response.streaming_content)
        self.assertTrue(contenido.startswith(b'%PDF'))
        table_rows = table_spy.call_args.args[0]
        texto_tabla = ' '.join(
            celda.getPlainText()
            for fila in table_rows
            for celda in fila
        )
        self.assertIn('Cliente A', texto_tabla)
        self.assertNotIn('Cliente B confidencial', texto_tabla)

    def test_serializer_rechaza_fk_de_otra_empresa(self):
        response = self.client.post(
            reverse('obra-list'),
            {'cliente': self.cliente_b.pk, 'nombre': 'Obra externa', 'direccion': 'Calle'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_mismo_documento_se_permite_en_empresas_distintas(self):
        duplicado = Cliente.objects.create(
            empresa=self.otra_empresa,
            documento=self.cliente_a.documento,
            razon_social='Documento repetido en B',
            direccion='Calle B',
            ciudad='Medellín',
            email='duplicado@example.com',
            celular='3222222222',
        )
        self.assertNotEqual(duplicado.empresa_id, self.cliente_a.empresa_id)

    def test_lector_puede_consultar_me_pero_no_escribir(self):
        lector = crear_usuario_empresa('lector-a', self.empresa, Membresia.Rol.LECTOR)
        self.client.force_authenticate(lector)

        me = self.client.get(reverse('user-me'))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['empresa']['id'], self.empresa.pk)
        self.assertEqual(me.data['rol'], Membresia.Rol.LECTOR)

        response = self.client.post(
            reverse('cliente-list'),
            {
                'documento': 'DOC-LECTOR',
                'razon_social': 'No autorizado',
                'direccion': 'Calle',
                'ciudad': 'Bogotá',
                'email': 'lector@example.com',
                'celular': '3000000000',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_gestion_de_usuarios_crea_membresia_y_no_concede_staff(self):
        response = self.client.post(
            reverse('user-list'),
            {
                'username': 'nuevo-operador',
                'email': 'operador@example.com',
                'password': 'TestPassword-123!',
                'is_staff': True,
                'rol': Membresia.Rol.OPERADOR,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        usuario = get_user_model().objects.get(username='nuevo-operador')
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.membresia.empresa, self.empresa)
        self.assertEqual(usuario.membresia.rol, Membresia.Rol.OPERADOR)

        user_ids = {item['id'] for item in self.client.get(reverse('user-list')).data}
        self.assertNotIn(self.usuario_b.pk, user_ids)

    def test_sin_autenticacion_recibe_401(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(reverse('cliente-list')).status_code, 401)

    def test_descarga_documento_requiere_tenant_y_no_hay_media_publica(self):
        media_dir = TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        documento = ClienteDocumento.objects.create(
            cliente=self.cliente_b,
            tipo=ClienteDocumento.Tipo.RUT,
            archivo=SimpleUploadedFile('confidencial.pdf', b'contenido privado'),
        )
        download_url = reverse('cliente-documento-archivo', args=[documento.pk])

        self.assertEqual(self.client.get(download_url).status_code, 404)
        self.client.force_authenticate(self.usuario_b)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'contenido privado')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(self.client.get(f'/media/{documento.archivo.name}').status_code, 404)

        producto = Producto.objects.create(
            empresa=self.cliente_b.empresa,
            tipo_producto=TipoProducto.objects.create(
                empresa=self.otra_empresa, nombre='Tipo con manual B',
            ),
            descripcion='Producto con archivos privados',
            manual=SimpleUploadedFile('manual.pdf', b'manual privado'),
            ficha_tecnica=SimpleUploadedFile('ficha.pdf', b'ficha privada'),
        )
        self.client.force_authenticate(self.usuario)
        self.assertEqual(
            self.client.get(reverse('producto-manual', args=[producto.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse('producto-ficha-tecnica', args=[producto.pk])).status_code,
            404,
        )

    def test_acciones_con_ids_ajenos_responden_404_o_400(self):
        remision = Remision.objects.create(
            empresa=self.otra_empresa,
            cliente=self.cliente_b,
            fecha_entrega_programada=date(2026, 10, 1),
        )
        factura = Factura.objects.create(
            empresa=self.otra_empresa,
            numero='FAC-B-1',
            cliente=self.cliente_b,
        )
        transportador = Transportador.objects.create(
            empresa=self.otra_empresa,
            nombre='Transportador B',
            documento='TRANS-B',
        )
        viaje = Viaje.objects.create(
            empresa=self.otra_empresa,
            transportador=transportador,
            destino='Medellín',
            fecha_salida='2026-10-01T10:00:00Z',
        )
        proveedor = Proveedor.objects.create(
            empresa=self.otra_empresa,
            nombre='Proveedor B',
            nit='PROV-B',
        )
        entrada = Entrada.objects.create(empresa=self.otra_empresa, proveedor=proveedor)
        salida = Salida.objects.create(empresa=self.otra_empresa, tipo=Salida.Tipo.VENTA)

        self.assertEqual(
            self.client.post(reverse('remision-confirmar', args=[remision.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('factura-pagar', args=[factura.pk]), {'monto': '1.00'}).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse('viaje-remision-list'),
                {'viaje': viaje.pk, 'remision': remision.pk},
                format='json',
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(reverse('remision-reservar', args=[remision.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('remision-cancelar', args=[remision.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('entrada-confirmar', args=[entrada.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('salida-completar', args=[salida.pk])).status_code,
            404,
        )

    def _crear_corpus_tenant_b(self):
        from datetime import date, datetime, timezone as dt_timezone
        from decimal import Decimal

        from cotizaciones.models import Cotizacion, CotizacionDetalle
        from devoluciones.models import Devolucion, DevolucionDetalle
        from facturas.models import FacturaDetalle, FacturaPago
        from kardex.models import KardexDetalle, KardexMovimiento
        from obras.models import Obra
        from orden_compra.models import (
            EntradaDetalle, Inventario, Lote, MovimientoInventario,
            OrdenCompra, OrdenCompraDetalle, SalidaDetalle,
        )
        from prestamos.models import EquipoObra, Prestamo, PrestamoDetalle
        from productos.models import Producto, ProductoProveedor
        from remisiones.models import RemisionAlarma, RemisionDetalle, RemisionReserva
        from responsables.models import Responsable
        from transportadores.models import (
            TransportadorVehiculo, ViajeRemision, Vehiculo,
        )

        empresa = self.otra_empresa
        tipo = TipoProducto.objects.create(empresa=empresa, nombre='Tipo corpus B')
        producto = Producto.objects.create(
            empresa=empresa, tipo_producto=tipo, descripcion='Producto corpus B',
        )
        proveedor = Proveedor.objects.create(
            empresa=empresa, nombre='Proveedor corpus B', nit='PROV-CORPUS-B',
        )
        responsable = Responsable.objects.create(
            empresa=empresa, documento='RESP-CORPUS-B', nombre='Ana', apellido='B',
        )
        obra = Obra.objects.create(
            cliente=self.cliente_b, nombre='Obra corpus B', direccion='Calle B',
        )
        documento = ClienteDocumento.objects.create(
            cliente=self.cliente_b,
            tipo=ClienteDocumento.Tipo.RUT,
            archivo=SimpleUploadedFile('tenant-b.pdf', b'tenant-b'),
        )
        transportador = Transportador.objects.create(
            empresa=empresa, nombre='Transportador corpus B', documento='TRANS-CORPUS-B',
        )
        vehiculo = Vehiculo.objects.create(
            empresa=empresa, placa='CORPUS-B', tipo=Vehiculo.Tipo.CAMION,
        )
        asignacion = TransportadorVehiculo.objects.create(
            transportador=transportador, vehiculo=vehiculo,
        )
        remision = Remision.objects.create(
            empresa=empresa, cliente=self.cliente_b, transportador=transportador,
            fecha_entrega_programada=date(2026, 10, 10),
        )
        remision_detalle = RemisionDetalle.objects.create(
            remision=remision, producto=producto, descripcion=producto.descripcion,
            cantidad=Decimal('1'), precio_unitario=Decimal('2'),
        )
        reserva = RemisionReserva.objects.create(remision=remision)
        alarma = RemisionAlarma.objects.create(
            remision=remision, tipo='TEST', descripcion='Alarma corpus B',
        )
        viaje = Viaje.objects.create(
            empresa=empresa, transportador=transportador, vehiculo=vehiculo,
            destino='Medellín', fecha_salida=datetime(2026, 10, 10, tzinfo=dt_timezone.utc),
        )
        viaje_remision = ViajeRemision.objects.create(viaje=viaje, remision=remision)
        cotizacion = Cotizacion.objects.create(empresa=empresa, cliente=self.cliente_b)
        cotizacion_detalle = CotizacionDetalle.objects.create(
            cotizacion=cotizacion, producto=producto, descripcion=producto.descripcion,
            cantidad=Decimal('1'), precio_unitario=Decimal('2'),
        )
        factura = Factura.objects.create(
            empresa=empresa, numero='FAC-CORPUS-B', cliente=self.cliente_b,
        )
        factura_detalle = FacturaDetalle.objects.create(
            factura=factura, producto=producto, descripcion=producto.descripcion,
            cantidad=Decimal('1'), precio_unitario=Decimal('2'),
        )
        factura_pago = FacturaPago.objects.create(
            factura=factura, metodo_pago=Factura.MetodoPago.EFECTIVO, monto=Decimal('1'),
        )
        devolucion = Devolucion.objects.create(
            empresa=empresa, cliente=self.cliente_b, obra=obra,
            transportador=transportador,
        )
        devolucion_detalle = DevolucionDetalle.objects.create(
            devolucion=devolucion, producto=producto, cantidad=Decimal('1'),
            motivo=DevolucionDetalle.Motivo.OTRO,
        )
        prestamo = Prestamo.objects.create(
            empresa=empresa, cliente=self.cliente_b, obra=obra,
            fecha_reserva=date(2026, 10, 10), estado=Prestamo.Estado.ACTIVO,
        )
        prestamo_detalle = PrestamoDetalle.objects.create(
            prestamo=prestamo, producto=producto,
            cantidad=Decimal('1'), precio_unitario=Decimal('1'),
        )
        equipo_obra = EquipoObra.objects.create(
            cliente=self.cliente_b, obra=obra, producto=producto,
        )
        movimiento_kardex = KardexMovimiento.objects.create(
            empresa=empresa, cliente=self.cliente_b,
            tipo=KardexMovimiento.Tipo.VENTA, valor=Decimal('2'),
        )
        kardex_detalle = KardexDetalle.objects.create(
            movimiento=movimiento_kardex, producto=producto,
            cantidad=Decimal('1'), precio_unitario=Decimal('1'),
        )
        orden = OrdenCompra.objects.create(
            empresa=empresa, proveedor=proveedor, fecha_entrega_programada=date(2026, 10, 10),
        )
        orden_detalle = OrdenCompraDetalle.objects.create(
            orden_compra=orden, producto=producto, cantidad=Decimal('1'),
            precio_unitario=Decimal('2'),
        )
        entrada = Entrada.objects.create(empresa=empresa, proveedor=proveedor)
        entrada_detalle = EntradaDetalle.objects.create(
            entrada=entrada, producto=producto, cantidad=Decimal('1'),
            precio_unitario=Decimal('2'),
        )
        inventario = Inventario.objects.create(producto=producto, proveedor=proveedor)
        salida = Salida.objects.create(
            empresa=empresa, cliente=self.cliente_b, responsable=responsable,
            tipo=Salida.Tipo.VENTA,
        )
        salida_detalle = SalidaDetalle.objects.create(
            salida=salida, producto=producto, cantidad=Decimal('1'),
            precio_unitario=Decimal('2'),
        )
        movimiento_inventario = MovimientoInventario.objects.create(
            producto=producto, tipo=MovimientoInventario.Tipo.ENTRADA,
            cantidad=Decimal('1'),
        )
        lote = Lote.objects.create(producto=producto, codigo='LOTE-CORPUS-B')
        producto_proveedor = ProductoProveedor.objects.create(
            producto=producto, proveedor=proveedor,
        )

        return {
            type(obj): obj for obj in (
                self.cliente_b, documento, tipo, producto, proveedor, responsable,
                obra, producto_proveedor, transportador, vehiculo, asignacion,
                viaje, viaje_remision, remision, remision_detalle, reserva, alarma,
                cotizacion, cotizacion_detalle, factura, factura_detalle, factura_pago,
                devolucion, devolucion_detalle, prestamo, prestamo_detalle, equipo_obra,
                movimiento_kardex, kardex_detalle, orden, orden_detalle, entrada,
                entrada_detalle, inventario, salida, salida_detalle,
                movimiento_inventario, lote, self.usuario_b,
            )
        }

    def test_listar_y_detalle_de_todos_los_routers_no_filtran_otro_tenant(self):
        from clientes.urls import router as clientes_router
        from cotizaciones.urls import router as cotizaciones_router
        from devoluciones.urls import router as devoluciones_router
        from facturas.urls import router as facturas_router
        from kardex.urls import router as kardex_router
        from obras.urls import router as obras_router
        from orden_compra.urls import router as compras_router
        from prestamos.urls import router as prestamos_router
        from productos.urls import router as productos_router
        from remisiones.urls import router as remisiones_router
        from responsables.urls import router as responsables_router
        from transportadores.urls import router as transporte_router
        from usuarios.urls import router as usuarios_router

        media_dir = TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        foreign_objects = self._crear_corpus_tenant_b()
        routers = (
            productos_router, clientes_router, obras_router, kardex_router,
            prestamos_router, transporte_router, facturas_router, remisiones_router,
            compras_router, cotizaciones_router, devoluciones_router,
            responsables_router, usuarios_router,
        )
        revisados = 0
        for router in routers:
            for _prefix, viewset, basename in router.registry:
                model = viewset.queryset.model
                foreign_object = foreign_objects.get(model)
                self.assertIsNotNone(
                    foreign_object,
                    f'Falta fixture de empresa B para el endpoint {basename} ({model.__name__}).',
                )

                list_response = self.client.get(reverse(f'{basename}-list'))
                self.assertEqual(list_response.status_code, 200, basename)
                payload = list_response.data
                rows = payload.get('results', []) if isinstance(payload, dict) else payload
                ids = {row.get('id') for row in rows if isinstance(row, dict)}
                self.assertNotIn(foreign_object.pk, ids, f'Fuga en listado {basename}.')

                detail_url = reverse(f'{basename}-detail', args=[foreign_object.pk])
                self.assertEqual(self.client.get(detail_url).status_code, 404, basename)
                patch_response = self.client.patch(detail_url, {}, format='json')
                self.assertIn(patch_response.status_code, (404, 405), basename)
                delete_response = self.client.delete(detail_url)
                self.assertIn(delete_response.status_code, (404, 405), basename)
                revisados += 1

        self.assertGreaterEqual(revisados, 35)

    def test_exportaciones_de_producto_e_inventario_son_accesibles_sin_fuga(self):
        media_dir = TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self._crear_corpus_tenant_b()

        for route_name in (
            'producto-exportar-pdf',
            'inventario-exportar-pdf',
            'inventario-exportar-excel',
        ):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200, route_name)

    def test_kardex_cliente_no_permite_consultar_cliente_de_otro_tenant(self):
        response = self.client.get(reverse('cliente-kardex', args=[self.cliente_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_saldo_no_acepta_id_de_cliente_de_otro_tenant(self):
        response = self.client.get(
            reverse('kardex-movimiento-saldo'),
            {'cliente': self.cliente_b.pk},
        )
        self.assertEqual(response.status_code, 404)

    def test_todas_las_acciones_post_de_detalle_ocultan_recursos_ajenos(self):
        from clientes.urls import router as clientes_router
        from cotizaciones.urls import router as cotizaciones_router
        from devoluciones.urls import router as devoluciones_router
        from facturas.urls import router as facturas_router
        from kardex.urls import router as kardex_router
        from obras.urls import router as obras_router
        from orden_compra.urls import router as compras_router
        from prestamos.urls import router as prestamos_router
        from productos.urls import router as productos_router
        from remisiones.urls import router as remisiones_router
        from responsables.urls import router as responsables_router
        from transportadores.urls import router as transporte_router
        from usuarios.urls import router as usuarios_router

        foreign_objects = self._crear_corpus_tenant_b()
        routers = (
            productos_router, clientes_router, obras_router, kardex_router,
            prestamos_router, transporte_router, facturas_router, remisiones_router,
            compras_router, cotizaciones_router, devoluciones_router,
            responsables_router, usuarios_router,
        )
        comprobadas = 0
        for router in routers:
            for _prefix, viewset, basename in router.registry:
                foreign_object = foreign_objects[viewset.queryset.model]
                for extra_action in viewset.get_extra_actions():
                    mapping = getattr(extra_action, 'mapping', {})
                    if not extra_action.detail or 'post' not in mapping:
                        continue
                    url = reverse(
                        f'{basename}-{extra_action.url_name}',
                        args=[foreign_object.pk],
                    )
                    response = self.client.post(url, {}, format='json')
                    self.assertEqual(
                        response.status_code,
                        404,
                        f'Acción ajena accesible: {basename}.{extra_action.__name__}',
                    )
                    comprobadas += 1

        self.assertGreaterEqual(comprobadas, 20)
