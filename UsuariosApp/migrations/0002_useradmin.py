from django.db import migrations
from django.contrib.auth.hashers import make_password


def crear_admin_por_defecto(apps, schema_editor):
    UsuarioSistema = apps.get_model("UsuariosApp", "UsuarioSistema")

    if not UsuarioSistema.objects.filter(username="admin").exists():
        UsuarioSistema.objects.create(
            username="admin",
            email="admin@teknetau.cl",
            role="admin",
            is_active=True,
            # 👇 encriptamos la contraseña igual que set_password
            password=make_password("admin123"),
            # 👇 y dejamos la visible en texto plano
            password_visible="admin123",
        )


def eliminar_admin(apps, schema_editor):
    UsuarioSistema = apps.get_model("UsuariosApp", "UsuarioSistema")
    UsuarioSistema.objects.filter(username="admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("UsuariosApp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_admin_por_defecto, eliminar_admin),
    ]