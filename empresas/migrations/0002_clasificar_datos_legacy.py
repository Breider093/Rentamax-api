from django.db import migrations


MODELOS_DIRECTOS = [
    ('clientes', 'Cliente'),
    ('productos', 'TipoProducto'),
    ('productos', 'Producto'),
    ('productos', 'Proveedor'),
    ('transportadores', 'Transportador'),
    ('transportadores', 'Vehiculo'),
    ('responsables', 'Responsable'),
    ('transportadores', 'Viaje'),
    ('remisiones', 'Remision'),
    ('facturas', 'Factura'),
    ('cotizaciones', 'Cotizacion'),
    ('devoluciones', 'Devolucion'),
    ('prestamos', 'Prestamo'),
    ('kardex', 'KardexMovimiento'),
    ('orden_compra', 'OrdenCompra'),
    ('orden_compra', 'Entrada'),
    ('orden_compra', 'Salida'),
]


def asignar_empresa_pendiente(apps, schema_editor):
    Empresa = apps.get_model('empresas', 'Empresa')
    alias = schema_editor.connection.alias
    empresa, _ = Empresa.objects.using(alias).get_or_create(
        nit='LEGACY-UNASSIGNED',
        defaults={
            'nombre': 'Datos legacy sin asignar',
            'activa': False,
        },
    )
    if empresa.activa:
        Empresa.objects.using(alias).filter(pk=empresa.pk).update(activa=False)

    for app_label, model_name in MODELOS_DIRECTOS:
        Modelo = apps.get_model(app_label, model_name)
        Modelo.objects.using(alias).filter(empresa__isnull=True).update(
            empresa_id=empresa.pk,
        )


def desasignar_empresa_pendiente(apps, schema_editor):
    Empresa = apps.get_model('empresas', 'Empresa')
    alias = schema_editor.connection.alias
    empresa = Empresa.objects.using(alias).filter(nit='LEGACY-UNASSIGNED').first()
    if not empresa:
        return
    for app_label, model_name in MODELOS_DIRECTOS:
        Modelo = apps.get_model(app_label, model_name)
        Modelo.objects.using(alias).filter(empresa_id=empresa.pk).update(empresa_id=None)
    empresa.delete(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ('empresas', '0001_initial'),
        ('clientes', '0002_cliente_empresa_alter_cliente_documento_and_more'),
        ('cotizaciones', '0003_cotizacion_empresa_alter_cotizacion_numero_and_more'),
        ('devoluciones', '0002_devolucion_empresa_alter_devolucion_numero_and_more'),
        ('facturas', '0005_factura_empresa_alter_factura_numero_and_more'),
        ('kardex', '0005_kardexmovimiento_empresa'),
        ('orden_compra', '0005_entrada_empresa_ordencompra_empresa_salida_empresa_and_more'),
        ('prestamos', '0003_prestamo_empresa'),
        ('productos', '0004_producto_empresa_proveedor_empresa_and_more'),
        ('remisiones', '0003_remision_empresa_alter_remision_numero_and_more'),
        ('responsables', '0002_responsable_empresa_alter_responsable_documento_and_more'),
        ('transportadores', '0004_transportador_empresa_vehiculo_empresa_viaje_empresa_and_more'),
    ]

    operations = [
        migrations.RunPython(asignar_empresa_pendiente, desasignar_empresa_pendiente),
    ]