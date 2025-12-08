from django.urls import path
from . import views

app_name = "facturacionapp"

urlpatterns = [
    path("", views.lista_documentos, name="lista_documentos"),
    path("nuevo/", views.crear_documento, name="crear_documento"),
    path("editar/<int:pk>/", views.editar_documento_post, name="editar_documento_post"),
    path("eliminar/<int:pk>/", views.eliminar_documento, name="eliminar_documento"),

    # API GET por PK
    path("api/documento/<int:pk>/", views.api_get_documento, name="api_get_documento"),

    # 🔥 NUEVO ENDPOINT
    path("proyecto/<int:proyecto_id>/documentos/", 
         views.api_documentos_por_proyecto, 
         name="api_documentos_por_proyecto"),

    path("export/pdf/", views.export_pdf_all, name="export_pdf_all"),
    path("export/excel/", views.export_excel_all, name="export_excel_all"),

    path("api/documento/<int:doc_id>/quitar/", views.api_quitar_documento, name="api_quitar_documento"),

]
