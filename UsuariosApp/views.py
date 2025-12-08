import random
import string

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ActualizarPasswordForm,
    ActualizarRolForm,
    SolicitarRecuperacionForm,
    UsuarioSistemaForm,
    VerificarCodigoForm,
)
from .models import PasswordResetCode, UsuarioSistema


# =========================
#   GESTIÓN DE USUARIOS
# =========================
def usuarios_admin(request):
    """
    Vista de administración de usuarios:
    - Listar todos
    - Crear nuevos
    """
    if request.session.get("user_role") != "admin":
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("dashboard")

    usuarios = UsuarioSistema.objects.all().order_by("username")
    form_creacion = UsuarioSistemaForm(request.POST or None)

    # Crear usuario
    if request.method == "POST" and request.POST.get("accion") == "crear":
        if form_creacion.is_valid():
            usuario = form_creacion.save()
            messages.success(
                request,
                f"Usuario '{usuario.username}' creado correctamente."
            )
            return redirect("usuariosapp:usuarios_admin")
        messages.error(request, "Corrige los errores del formulario.")

    context = {
        "usuarios": usuarios,
        "form_creacion": form_creacion,
    }
    return render(request, "usuarios/administrar_usuarios.html", context)


def actualizar_rol(request, pk):
    """
    Actualiza rol e is_active de un usuario.
    """
    if request.session.get("user_role") != "admin":
        messages.error(request, "No tienes permisos para modificar roles.")
        return redirect("dashboard")

    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    form = ActualizarRolForm(request.POST or None, instance=usuario)

    if request.method == "POST":
        # Manejo manual del checkbox is_active
        data = request.POST.copy()
        data["is_active"] = "True" if request.POST.get("is_active") == "True" else "False"
        form = ActualizarRolForm(data, instance=usuario)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Rol de '{usuario.username}' actualizado correctamente."
            )
        else:
            messages.error(request, "No se pudo actualizar el rol.")

    return redirect("usuariosapp:usuarios_admin")


def actualizar_password(request, pk):
    if request.session.get("user_role") != "admin":
        messages.error(request, "No tienes permisos para cambiar contraseñas.")
        return redirect("dashboard")

    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    form = ActualizarPasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        # ✅ Solo guardamos la contraseña encriptada
        usuario.set_password(form.cleaned_data["password"])
        usuario.save(update_fields=["password"])

        messages.success(request, f"Contraseña de '{usuario.username}' actualizada.")
    else:
        if request.method == "POST":
            messages.error(request, "No se pudo actualizar la contraseña.")

    return redirect("usuariosapp:usuarios_admin")


def eliminar_usuario(request, pk):
    """
    Elimina físicamente al usuario de la BD.
    """
    if request.session.get("user_role") != "admin":
        messages.error(request, "No tienes permisos para eliminar usuarios.")
        return redirect("dashboard")

    usuario = get_object_or_404(UsuarioSistema, pk=pk)

    if request.method == "POST":
        nombre = usuario.username
        usuario.delete()
        messages.warning(request, f"Usuario '{nombre}' eliminado correctamente.")
        return redirect("usuariosapp:usuarios_admin")

    return redirect("usuariosapp:usuarios_admin")


def logout_view(request):
    """
    Cierra sesión y limpia la sesión.
    """
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("login")


# =========================
#   RECUPERACIÓN PASSWORD
# =========================
def _generar_codigo(longitud: int = 6) -> str:
    """Genera un código numérico de N dígitos."""
    return "".join(random.choices(string.digits, k=longitud))


def _generar_password_temporal(longitud: int = 8) -> str:
    """Genera una contraseña alfanumérica de un solo uso."""
    caracteres = string.ascii_letters + string.digits
    return "".join(random.choices(caracteres, k=longitud))


def solicitar_recuperacion(request):
    """
    El usuario ingresa su nombre de usuario y, si existe y tiene correo,
    se envía una contraseña temporal de un solo uso al correo asociado.
    """
    form = SolicitarRecuperacionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario = form.user  # set en clean_usuario del form
        password_temporal = _generar_password_temporal()

        PasswordResetCode.objects.create(user=usuario, code=password_temporal)

        asunto = "Recuperación de acceso TEKNETAU"
        mensaje = (
            "Has solicitado recuperar tu acceso en TEKNETAU.\n\n"
            "Te enviamos una contraseña temporal de un solo uso:\n"
            f"{password_temporal}\n\n"
            "Esta contraseña caduca en 15 minutos y deja de funcionar en cuanto inicies sesión.\n"
            "Úsala como contraseña en el inicio de sesión para entrar a la aplicación."
            " Si no solicitaste este acceso, puedes ignorar este mensaje."
        )

        # IMPORTANTE: asegúrate de tener bien configurado EMAIL_* en settings
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,  # Si falla, queremos ver el error en consola
        )

        messages.success(
            request,
            "Hemos enviado una contraseña temporal a tu correo. Úsala para iniciar sesión.",
        )
        return redirect("login")

    return render(request, "login/solicitar_recuperacion.html", {"form": form})


def verificar_codigo(request):
    """
    Paso 2: el usuario ingresa:
    - usuario
    - código
    - nueva contraseña
    """
    form = VerificarCodigoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario = get_object_or_404(
            UsuarioSistema,
            username=form.cleaned_data["usuario"],
            is_active=True,  # si no está activo, no puede recuperar ni entrar
        )

        try:
            codigo_obj = PasswordResetCode.objects.filter(
                user=usuario,
                code=form.cleaned_data["codigo"],
            ).latest("created_at")
        except PasswordResetCode.DoesNotExist:
            codigo_obj = None

        if codigo_obj and codigo_obj.is_valid():
            # Actualizar password
            usuario.set_password(form.cleaned_data["nueva_password"])
            usuario.save(update_fields=["password", "password_visible"])

            # Marcar código como usado
            codigo_obj.used = True
            codigo_obj.save(update_fields=["used"])

            messages.success(
                request,
                "Contraseña actualizada correctamente. Ya puedes iniciar sesión."
            )
            return redirect("login")

        messages.error(
            request,
            "Código inválido o expirado. Solicita uno nuevo e inténtalo nuevamente."
        )

    return render(request, "login/verificar_codigo.html", {"form": form})