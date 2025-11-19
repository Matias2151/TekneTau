"""
URL configuration for EmpresaPersona project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from EmpresaPersonaApp import views as empresa_views

urlpatterns = [
    # Administración␊
    path('admin/', admin.site.urls),

    # ✅ Página principal → INDEX␊
    path('', empresa_views.index, name='index'),

    # Login y Dashboard␊
    path('login/', empresa_views.login_view, name='login'),
    path('dashboard/', empresa_views.dashboard, name='dashboard'),

    # Aplicaciones internas␊
    path('empresapersona/', include('EmpresaPersonaApp.urls')),
    path('direccion/', include('DireccionApp.urls')),
    path('productoyservicio/', include('ProductoServicioApp.urls')),
    path('proyectos/', include('ProyectoApp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)