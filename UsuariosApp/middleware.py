from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class RoleRequiredMiddleware:
    """Controla el acceso según el rol almacenado en la sesión."""

    def __init__(self, get_response):
        self.get_response = get_response

        # Vistas siempre accesibles para todos (aunque no estén logueados)
        self.allowed_for_all = {
            "index",
            "login",
            "usuariosapp:logout",
            "usuariosapp:solicitar_recuperacion",
            "usuariosapp:verificar_codigo",
        }

        # Rutas por prefijo que siempre se permiten (estáticos, admin, etc.)
        self.allowed_prefixes = (
            "/static/",
            "/admin/",
        )

    def __call__(self, request):
        path = request.path

        # 1) Permitir estáticos y admin sin validar rol
        if path.startswith(self.allowed_prefixes):
            return self.get_response(request)

        # 2) Obtener nombre de la vista (view_name)
        resolver_match = request.resolver_match
        view_name = resolver_match.view_name if resolver_match else None

        # Si no sabemos la vista, seguimos normal (evita romper cosas raras)
        if view_name is None:
            return self.get_response(request)

        # 3) Vistas públicas (index, login, recuperar contraseña...)
        if view_name in self.allowed_for_all:
            return self.get_response(request)

        # 4) Verificar sesión
        user_role = request.session.get("user_role")
        if not user_role:
            return redirect("login")

        # 5) Admin -> acceso total
        if user_role == "admin":
            return self.get_response(request)

        # 6) Contador -> solo dashboard + facturación + proyectos
        if user_role == "contador":
            if (
                path.startswith("/dashboard/")
                or path.startswith("/facturacion/")
                or path.startswith("/proyectos/")
            ):
                return self.get_response(request)

            # Si llegó aquí, no tiene permiso
            messages.warning(
                request,
                "No tienes permisos para acceder a esta sección.",
            )
            return redirect("dashboard")

        # 7) Cualquier otro rol desconocido
        messages.error(request, "Rol no reconocido, inicia sesión nuevamente.")
        return redirect("login")
