# EmpresaPersonaApp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db import transaction
from .models import EmpresaPersona
from .forms import EmpresaPersonaForm
from DireccionApp.models import Direccion
from DireccionApp.forms import DireccionForm

# ✅ VISTA PRINCIPAL (única)
@transaction.atomic
def empresa_clientes(request):
    personas = EmpresaPersona.objects.select_related(
        "emppe_dire__regi", "emppe_dire__ciuda", "emppe_dire__comun"
    ).all()

    if request.method == "POST":
        form_p = EmpresaPersonaForm(request.POST)
        form_d = DireccionForm(request.POST)
        if form_p.is_valid() and form_d.is_valid():
            direccion = form_d.save()
            persona = form_p.save(commit=False)
            persona.emppe_dire = direccion
            persona.save()
            return redirect("empresa_clientes")
        # ❗Si hay errores, se vuelve a renderizar con los formularios con errores
        context = {
            "personas": personas,
            "form_p": form_p,
            "form_d": form_d,
            "open_modal": True, # 👈 Abre el modal al guardar correctamente
        }
        return render(request, "empresa_persona/empresa_clientes.html", context)

    # GET normal
    context = {
        "personas": personas,
        "form_p": EmpresaPersonaForm(),
        "form_d": DireccionForm(),
    }
    return render(request, "empresa_persona/empresa_clientes.html", context)




# ✅ EDITAR
@transaction.atomic
def editar_persona(request, pk):
    persona = get_object_or_404(EmpresaPersona, pk=pk)
    direccion = persona.emppe_dire

    if request.method == "POST":
        form_p = EmpresaPersonaForm(request.POST, instance=persona)
        form_d = DireccionForm(request.POST, instance=direccion)
        if form_p.is_valid() and form_d.is_valid():
            form_d.save()
            form_p.save()
            return redirect("empresa_clientes")

    # En caso de error o GET forzado
    return redirect("empresa_clientes")


# ✅ ELIMINAR
@transaction.atomic
def eliminar_persona(request, pk):
    persona = get_object_or_404(EmpresaPersona, pk=pk)
    if request.method == "POST":
        persona.delete()
        return redirect("empresa_clientes")
    return JsonResponse({"error": "Método no permitido"}, status=405)



def index(request):
    return render(request, 'inicio/index.html')


def login_view(request):
    return render(request, 'login/login.html')

def dashboard(request):
    return render(request, 'login/dashboard.html')

# ✅ API JSON para obtener lista de personas (para AJAX o Fetch)
def obtener_personas_json(request):
    """
    Devuelve todas las empresas/personas en formato JSON.
    Ideal para usar con fetch() o DataTables en empresa_clientes.html.
    """
    personas = EmpresaPersona.objects.select_related(
        "emppe_dire__regi", "emppe_dire__ciuda", "emppe_dire__comun"
    ).all()

    data = []
    for p in personas:
        data.append({
            "id": p.emppe_id,
            "rut": p.emppe_rut,
            "nombre": p.emppe_nom,
            "alias": p.emppe_alias or "",
            "fono1": p.emppe_fono1,
            "fono2": p.emppe_fono2 or "",
            "mail1": p.emppe_mail1,
            "mail2": p.emppe_mail2 or "",
            "estado": "Activo" if p.emppe_est else "Inactivo",
            "situacion": p.emppe_sit,
            "direccion": {
                "calle": p.emppe_dire.dire_calle if p.emppe_dire else "",
                "num": p.emppe_dire.dire_num if p.emppe_dire else "",
                "otros": p.emppe_dire.dire_otros if p.emppe_dire else "",
                "region": p.emppe_dire.regi.regi_nom if p.emppe_dire and p.emppe_dire.regi else "",
                "ciudad": p.emppe_dire.ciuda.ciuda_nom if p.emppe_dire and p.emppe_dire.ciuda else "",
                "comuna": p.emppe_dire.comun.comun_nom if p.emppe_dire and p.emppe_dire.comun else "",
                "codigo_postal": p.emppe_dire.dire_cod_postal if p.emppe_dire else "",
            },
        })

    return JsonResponse(data, safe=False)