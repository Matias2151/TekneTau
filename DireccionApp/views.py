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
        .filter(regi_id=regi_id)  # o regi__regi_id=regi_id según tu modelo
        .values('ciuda_id', 'ciuda_nom')
        .order_by('ciuda_nom')
    )
    return JsonResponse(list(ciudades), safe=False)


# 🔹 Listar comunas según ciudad seleccionada
def comunas_por_ciudad(request, ciuda_id):
    """
    Devuelve las comunas asociadas a una ciudad.
    Regla práctica: si el usuario eligió Santiago (ciuda_id=22),
    también se muestran comunas de provincias vecinas (23..27).
    """
    ciuda_id = int(ciuda_id)

    if ciuda_id == 22:
        comunas_qs = (
            Comuna.objects
            .filter(ciuda_id__in=[22, 23, 24, 25, 26, 27])
            .values('comun_id', 'comun_nom')
            .order_by('comun_nom')
        )
    else:
        comunas_qs = (
            Comuna.objects
            .filter(ciuda_id=ciuda_id)
            .values('comun_id', 'comun_nom')
            .order_by('comun_nom')
        )

    return JsonResponse(list(comunas_qs), safe=False)
