# ProyectoApp/urls.py
from django.urls import path
from . import views

app_name = "proyectoapp"

urlpatterns = [
    path("", views.lista_proyectos, name="lista_proyectos"),
    path("crear/", views.crear_proyecto, name="crear_proyecto"),
    path("editar/<int:pk>/", views.editar_proyecto, name="editar_proyecto"),
    path("eliminar/<int:pk>/", views.eliminar_proyecto, name="eliminar_proyecto"),
    path("<int:pk>/detalle/", views.detalle_proyecto, name="detalle_proyecto"),
]