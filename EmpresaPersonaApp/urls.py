from django.urls import path
from . import views

urlpatterns = [
    path("empresa_clientes/", views.empresa_clientes, name="empresa_clientes"),
    path("editar/<int:pk>/", views.editar_persona, name="editar_persona"),
    path(
        "cambiar_estado/<int:pk>/",
        views.cambiar_estado_persona,
        name="cambiar_estado_persona",
    ),
    path("obtener_personas_json/", views.obtener_personas_json, name="obtener_personas_json"),
]