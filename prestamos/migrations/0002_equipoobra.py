import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0001_initial'),
        ('obras', '0001_initial'),
        ('prestamos', '0001_initial'),
        ('productos', '0003_producto_codigo'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipoObra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(blank=True, max_length=255)),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('fecha_inicio', models.DateField(blank=True, null=True)),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('ACTIVO', 'Activo'), ('EN_USO', 'En uso'), ('FINALIZADO', 'Finalizado')], default='ACTIVO', max_length=20)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='equipos_obra', to='clientes.cliente')),
                ('obra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='equipos_obra', to='obras.obra')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='equipos_obra', to='productos.producto')),
            ],
            options={
                'db_table': 'equipo_obra',
                'ordering': ['obra__nombre', 'producto__descripcion', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='equipoobra',
            index=models.Index(fields=['cliente', 'obra'], name='equipo_obra_cliente_obra_idx'),
        ),
        migrations.AddIndex(
            model_name='equipoobra',
            index=models.Index(fields=['estado'], name='equipo_obra_estado_idx'),
        ),
    ]
