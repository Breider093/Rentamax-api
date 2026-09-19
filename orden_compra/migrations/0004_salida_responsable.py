from django.db import migrations, models
import django.db.models.deletion


def clear_legacy_user_responsables(apps, schema_editor):
    Salida = apps.get_model('orden_compra', 'Salida')
    Salida.objects.update(responsable_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('orden_compra', '0003_inventario_reporte_fields'),
        ('responsables', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            clear_legacy_user_responsables,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='salida',
            name='responsable',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='salidas_responsable',
                to='responsables.responsable',
            ),
        ),
    ]
