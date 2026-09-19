import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orden_compra', '0002_salida_salidadetalle_lote_movimientoinventario_and_more'),
        ('productos', '0003_producto_codigo'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventario',
            name='codigo',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='inventario',
            name='descripcion',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='inventario',
            name='devolucion',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='en_alquiler',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='en_bodega',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='estado',
            field=models.CharField(default='Disponible', max_length=50),
        ),
        migrations.AddField(
            model_name='inventario',
            name='remision',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='reposicion',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='saldo_proveedor',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='inventario',
            name='proveedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='inventarios', to='productos.proveedor'),
        ),
    ]
