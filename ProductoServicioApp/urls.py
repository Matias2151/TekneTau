# ProductoServicioApp/urls.py
from django.urls import path
from . import views

app_name = 'productoyservicioapp'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path(
        'descargar-plantilla-productos/',
        views.descargar_plantilla_productos,
        name='descargar_plantilla_productos',
    ),
    path(
        'cargar-productos-excel/',
        views.cargar_productos_excel,
        name='cargar_productos_excel',
    ),
    path(
        'subir-excel-producto/<int:pk>/',
        views.subir_excel_producto,
        name='subir_excel_producto',
    ),
]
