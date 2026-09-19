from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0002_proveedor_productoproveedor_producto_proveedores_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='codigo',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
