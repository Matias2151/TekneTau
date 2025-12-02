# EmpresaPersonaApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Vista principal de Empresa/Persona (lista + creación en modal)
    path("empresa_clientes/", views.empresa_clientes, name="empresa_clientes"),

    # Editar datos del cliente/proveedor (se usa con el modal de edición)
    path("editar/<int:pk>/", views.editar_persona, name="editar_persona"),

    # Inhabilitar cliente/proveedor (antes "eliminar")
    path("eliminar/<int:pk>/", views.eliminar_persona, name="eliminar_persona"),

    # Habilitar cliente/proveedor previamente inhabilitado
    path("habilitar/<int:pk>/", views.habilitar_persona, name="habilitar_persona"),

    # Endpoint JSON opcional
    path("obtener_personas_json/", views.obtener_personas_json, name="obtener_personas_json"),
]
