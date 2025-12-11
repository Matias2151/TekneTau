from django.contrib.auth.hashers import make_password
from django.db import migrations


def ensure_admin_user(apps, schema_editor):
    UsuarioSistema = apps.get_model("UsuariosApp", "UsuarioSistema")

    # Crea o actualiza siempre el usuario administrador con credenciales conocidas
    UsuarioSistema.objects.update_or_create(
        username="admin",
        defaults={
            "email": "admin@teknetau.cl",
            "role": "admin",
            "is_active": True,
            "password": make_password("admin123"),
            "password_visible": "admin123",
        },
    )


def remove_admin_user(apps, schema_editor):
    UsuarioSistema = apps.get_model("UsuariosApp", "UsuarioSistema")
    UsuarioSistema.objects.filter(username__iexact="admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("UsuariosApp", "0002_useradmin"),
    ]

    operations = [
        migrations.RunPython(ensure_admin_user, remove_admin_user),
    ]
