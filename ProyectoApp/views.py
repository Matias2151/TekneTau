# ProyectoApp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from .models import Proyecto
from EmpresaPersonaApp.models import EmpresaPersona
from .forms import ProyectoForm


def es_ajax(request):
    """Detecta si la solicitud es AJAX (case-insensitive y compatible con fetch)."""
    return request.headers.get("x-requested-with", "").lower() == "xmlhttprequest"


# 🆕 Helper: obtener info del cliente asociada al proyecto
def _cliente_info(proyecto):
    """
    Devuelve un diccionario con la información del cliente asociada al proyecto.
    Intenta usar propiedades del modelo (cliente, cliente_nombre, etc.) y,
    si no existen, cae al objeto EmpresaPersona relacionado.
    """
    # Intentar usar propiedades directas si existen
    cliente_id = getattr(proyecto, "cliente_id", None)
    cliente_nombre = getattr(proyecto, "cliente_nombre", None)
    cliente_rut = getattr(proyecto, "cliente_rut", None)
    cliente_mail = getattr(proyecto, "cliente_mail", None)
    cliente_fono = getattr(proyecto, "cliente_fono", None)

    # Intentar obtener el objeto cliente/EmpresaPersona
    cliente_obj = getattr(proyecto, "cliente", None)
    if cliente_obj is None:
        # Por si el campo se llama distinto (ej: emppe, empresa, etc.)
        cliente_obj = getattr(proyecto, "emppe", None)

    if cliente_obj is not None:
        if cliente_id is None:
            cliente_id = getattr(cliente_obj, "emppe_id", None)
        if cliente_nombre is None:
            cliente_nombre = getattr(cliente_obj, "emppe_nom", None)
        if cliente_rut is None:
            cliente_rut = getattr(cliente_obj, "emppe_rut", None)
        if cliente_mail is None:
            cliente_mail = getattr(cliente_obj, "emppe_mail1", None)
        if cliente_fono is None:
            cliente_fono = getattr(cliente_obj, "emppe_fono1", None)

    return {
        "cliente_id": cliente_id or "",
        "cliente_nombre": cliente_nombre or "Sin asignar",
        "cliente_rut": cliente_rut or "—",
        "cliente_mail": cliente_mail or "—",
        "cliente_fono": cliente_fono or "—",
    }


# 🔹 LISTAR PROYECTOS
def lista_proyectos(request):
    """Vista principal: lista los proyectos y prepara el formulario para el modal."""
    proyectos = Proyecto.objects.all().order_by("-proye_idt")

    # 🔍 Clientes activos que sean cliente o ambos
    clientes = EmpresaPersona.objects.filter(
        emppe_est=True
    ).filter(
        Q(emppe_sit="cliente") | Q(emppe_sit="ambos")
    ).order_by("emppe_nom")

    contexto = {
        "proyectos": proyectos,
        "form": ProyectoForm(),
        "clientes": clientes,
    }
    # Asegúrate que este path coincide con tu template
    return render(request, "proyecto/proyecto.html", contexto)


# 🔹 CREAR PROYECTO
@transaction.atomic
def crear_proyecto(request):
    """Crea un nuevo proyecto (maneja AJAX y modo normal)."""
    if request.method != "POST":
        # ⛔ Usar __all__ para que el JS lo muestre como error general
        msg = {"__all__": ["Método no permitido."]}
        if es_ajax(request):
            return JsonResponse({"success": False, "errors": msg}, status=405)
        messages.error(request, "Método no permitido para esta ruta.")
        return redirect("proyectoapp:lista_proyectos")

    form = ProyectoForm(request.POST)
    if not form.is_valid():
        if es_ajax(request):
            # form.errors → dict con claves: proye_desc, proye_fecha_sol, etc.
            return JsonResponse({"success": False, "errors": form.errors})
        messages.error(request, "⚠️ Corrige los errores del formulario.")
        return redirect("proyectoapp:lista_proyectos")

    # 🔁 asignar cliente manualmente desde el <select name="cliente">
    proyecto = form.save(commit=False)

    cliente_id = request.POST.get("cliente")  # 👈 viene del select del template
    if cliente_id:
        try:
            # IMPORTANTE: FK real en tu modelo Proyecto
            proyecto.cliente = EmpresaPersona.objects.get(pk=cliente_id)
        except EmpresaPersona.DoesNotExist:
            if es_ajax(request):
                return JsonResponse(
                    {
                        "success": False,
                        "errors": {"cliente": ["El cliente seleccionado no existe."]},
                    },
                    status=400,
                )
            messages.error(request, "El cliente seleccionado no existe.")
            return redirect("proyectoapp:lista_proyectos")

    proyecto.save()

    # 🆕 info de cliente para usar en el frontend (Ver proyecto)
    cliente_data = _cliente_info(proyecto)

    # ✅ Si es AJAX
    if es_ajax(request):
        return JsonResponse({
            "success": True,
            "msg": "Proyecto creado correctamente.",
            "created": {
                "id": proyecto.proye_idt,
                "desc": proyecto.proye_desc,
                "obs": getattr(proyecto, "proye_obs", "") or "",
                # Fechas en formato YYYY-MM-DD para que JS las convierta
                "fecha_sol": proyecto.proye_fecha_sol.strftime("%Y-%m-%d")
                if getattr(proyecto, "proye_fecha_sol", None) else "",
                "fecha_ter": proyecto.proye_fecha_ter.strftime("%Y-%m-%d")
                if getattr(proyecto, "proye_fecha_ter", None) else "",
                "estado": proyecto.proye_estado,
                "cliente_id": cliente_data["cliente_id"],
                "cliente_nombre": cliente_data["cliente_nombre"],
                "cliente_rut": cliente_data["cliente_rut"],
                "cliente_mail": cliente_data["cliente_mail"],
                "cliente_fono": cliente_data["cliente_fono"],
            }
        })

    # Fallback tradicional
    messages.success(request, "✅ Proyecto creado correctamente.")
    return redirect("proyectoapp:lista_proyectos")


# 🔹 EDITAR PROYECTO
@transaction.atomic
def editar_proyecto(request, pk):
    """Edita un proyecto existente (maneja AJAX y fallback normal)."""
    proyecto = get_object_or_404(Proyecto, pk=pk)

    if request.method != "POST":
        msg = {"__all__": ["Método no permitido."]}
        if es_ajax(request):
            return JsonResponse({"success": False, "errors": msg}, status=405)
        messages.error(request, "Método no permitido para esta ruta.")
        return redirect("proyectoapp:lista_proyectos")

    form = ProyectoForm(request.POST, instance=proyecto)
    if not form.is_valid():
        if es_ajax(request):
            return JsonResponse({"success": False, "errors": form.errors})
        messages.error(request, "⚠️ Corrige los errores del formulario.")
        return redirect("proyectoapp:lista_proyectos")

    # 🔁 actualizar también el cliente desde el POST
    proyecto = form.save(commit=False)

    cliente_id = request.POST.get("cliente")
    if cliente_id:
        try:
            # 🔧 CORREGIDO: se asigna al FK cliente, no a emppe_nom
            proyecto.cliente = EmpresaPersona.objects.get(pk=cliente_id)
        except EmpresaPersona.DoesNotExist:
            if es_ajax(request):
                return JsonResponse(
                    {
                        "success": False,
                        "errors": {"cliente": ["El cliente seleccionado no existe."]},
                    },
                    status=400,
                )
            messages.error(request, "El cliente seleccionado no existe.")
            return redirect("proyectoapp:lista_proyectos")
    else:
        # Si quieres permitir proyectos sin cliente, puedes dejarlo así:
        # proyecto.cliente = None
        pass

    proyecto.save()

    # 🆕 info de cliente actualizada
    cliente_data = _cliente_info(proyecto)

    # ✅ AJAX → JSON
    if es_ajax(request):
        return JsonResponse({
            "success": True,
            "msg": "Proyecto actualizado correctamente.",
            "updated": {
                "id": proyecto.proye_idt,
                "desc": proyecto.proye_desc,
                "obs": getattr(proyecto, "proye_obs", "") or "",
                "fecha_sol": proyecto.proye_fecha_sol.strftime("%Y-%m-%d")
                if getattr(proyecto, "proye_fecha_sol", None) else "",
                "fecha_ter": proyecto.proye_fecha_ter.strftime("%Y-%m-%d")
                if getattr(proyecto, "proye_fecha_ter", None) else "",
                "estado": proyecto.proye_estado,
                "cliente_id": cliente_data["cliente_id"],
                "cliente_nombre": cliente_data["cliente_nombre"],
                "cliente_rut": cliente_data["cliente_rut"],
                "cliente_mail": cliente_data["cliente_mail"],
                "cliente_fono": cliente_data["cliente_fono"],
            }
        })

    # Modo normal
    messages.success(request, "✅ Proyecto actualizado correctamente.")
    return redirect("proyectoapp:lista_proyectos")


# 🔹 ELIMINAR PROYECTO
@transaction.atomic
def eliminar_proyecto(request, pk):
    """Elimina un proyecto existente (confirmación modal y AJAX)."""
    if request.method != "POST":
        msg = {"__all__": ["Método no permitido."]}
        if es_ajax(request):
            return JsonResponse({"success": False, "errors": msg}, status=405)
        messages.error(request, "Método no permitido para esta ruta.")
        return redirect("proyectoapp:lista_proyectos")

    proyecto = get_object_or_404(Proyecto, pk=pk)
    proyecto.delete()

    if es_ajax(request):
        return JsonResponse({"success": True, "msg": "🗑️ Proyecto eliminado correctamente."})

    messages.success(request, "🗑️ Proyecto eliminado correctamente.")
    return redirect("proyectoapp:lista_proyectos")


# 🔹 DETALLE OPCIONAL
def detalle_proyecto(request, pk):
    """Muestra detalles completos de un proyecto."""
    proyecto = get_object_or_404(Proyecto, pk=pk)
    clientes = EmpresaPersona.objects.filter(
        emppe_est=True
    ).filter(
        Q(emppe_sit="cliente") | Q(emppe_sit="ambos")
    ).order_by("emppe_nom")

    return render(
        request,
        "proyecto/detalle_proyecto.html",
        {"proyecto": proyecto, "clientes": clientes},
    )
