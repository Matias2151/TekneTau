from django.urls import path
from . import views

app_name = "usuariosapp"

urlpatterns = [
    # Panel de administración de usuarios
    path("", views.usuarios_admin, name="usuarios_admin"),

    # Sesión
    path("logout/", views.logout_view, name="logout"),

    # Gestión de rol / estado / contraseña
    path("rol/<int:pk>/", views.actualizar_rol, name="actualizar_rol"),
    path("password/<int:pk>/", views.actualizar_password, name="actualizar_password"),

    # 🔹 Eliminar usuario
    path("eliminar/<int:pk>/", views.eliminar_usuario, name="eliminar_usuario"),

    # Recuperación de contraseña
    path("recuperar/", views.solicitar_recuperacion, name="solicitar_recuperacion"),
    path("verificar/", views.verificar_codigo, name="verificar_codigo"),
]
