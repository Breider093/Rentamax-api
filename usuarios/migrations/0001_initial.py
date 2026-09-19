from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def crear_perfiles_existentes(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    UsuarioPerfil = apps.get_model('usuarios', 'UsuarioPerfil')
    UsuarioPerfil.objects.bulk_create(
        [UsuarioPerfil(usuario_id=usuario.id) for usuario in User.objects.all()],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UsuarioPerfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('documento', models.CharField(blank=True, max_length=27)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('cargo', models.CharField(blank=True, max_length=100)),
                ('estado', models.CharField(choices=[('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo')], default='ACTIVO', max_length=10)),
                ('empresa', models.CharField(blank=True, max_length=150)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'usuario_perfiles'},
        ),
        migrations.RunPython(crear_perfiles_existentes, migrations.RunPython.noop),
    ]
