# DireccionApp/views.py
from django.http import JsonResponse
from .models import Ciudad, Comuna

# 🔹 Listar ciudades según región seleccionada
def ciudades_por_region(request, regi_id):
    """
    Devuelve las ciudades que pertenecen a una región específica.
    Utilizado en los combobox dinámicos del formulario Dirección.
    """
    ciudades = (
        Ciudad.objects
        .filter(regi_id=regi_id)
        .values('ciuda_id', 'ciuda_nom')
        .order_by('ciuda_nom')
    )
    return JsonResponse(list(ciudades), safe=False)


# 🔹 Listar comunas según ciudad seleccionada
def comunas_por_ciudad(request, ciuda_id):
    """
    Devuelve las comunas asociadas a una ciudad.
    Utilizado en los combobox dinámicos del formulario Dirección.
    """
    comunas = (
        Comuna.objects
        .filter(ciuda_id=ciuda_id)
        .values('comun_id', 'comun_nom')
        .order_by('comun_nom')
    )
    return JsonResponse(list(comunas), safe=False)
