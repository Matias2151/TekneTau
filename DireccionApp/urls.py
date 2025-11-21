from django.urls import path
from . import views

urlpatterns = [
    path('ciudades/<int:regi_id>/', views.ciudades_por_region, name='ciudades_por_region'),
    path('comunas/<int:ciuda_id>/', views.comunas_por_ciudad, name='comunas_por_ciudad'),
]
