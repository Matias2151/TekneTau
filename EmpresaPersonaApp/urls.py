from django.urls import path
from . import views

urlpatterns = [
    path("empresa_clientes/", views.empresa_clientes, name="empresa_clientes"),
    path("editar/<int:pk>/", views.editar_persona, name="editar_persona"),
    path("eliminar/<int:pk>/", views.eliminar_persona, name="eliminar_persona"),
    path("obtener_personas_json/", views.obtener_personas_json, name="obtener_personas_json"),
]