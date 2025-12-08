# EmpresaPersonaApp/views.py
from django.db import transaction
from django.db.models import Count, F, OuterRef, Q, Sum
from django.db.models.expressions import Subquery
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages  

from UsuariosApp.forms import LoginForm
from UsuariosApp.models import PasswordResetCode,UsuarioSistema

from .models import EmpresaPersona
from .forms import EmpresaPersonaForm
from DireccionApp.models import Direccion
from DireccionApp.forms import DireccionForm
from FacturacionApp.models import DetalleDoc, Documento
from ProyectoApp.models import Proyecto


# ✅ VISTA PRINCIPAL (lista + crear)
@transaction.atomic
def empresa_clientes(request):
    """
    Vista principal de gestión de Empresa/Persona:
    - Lista todas las personas (clientes/proveedores)
    - Permite crear nuevas desde el modal.
    - Separa habilitados vs deshabilitados para usarlos en pestañas.
    """

    # Consultamos todas las personas con su dirección relacionada
    personas = EmpresaPersona.objects.select_related(
        "emppe_dire__regi", "emppe_dire__ciuda", "emppe_dire__comun"
    ).all()

    # Subgrupos por estado
    personas_habilitadas = personas.filter(emppe_est=True)
    personas_deshabilitadas = personas.filter(emppe_est=False)

    if request.method == "POST":
        # Formularios de creación
        form_p = EmpresaPersonaForm(request.POST)
        form_d = DireccionForm(request.POST)

        if form_p.is_valid() and form_d.is_valid():
            # Guardamos primero la dirección
            direccion = form_d.save()
            # Luego la persona, enlazando la dirección
            persona = form_p.save(commit=False)
            persona.emppe_dire = direccion
            persona.save()

            messages.success(
                request,
                f'Se ha creado el cliente/proveedor "{persona.emppe_nom}" correctamente.'
            )
            return redirect("empresa_clientes")

        # ❗Si hay errores, se vuelve a renderizar con los formularios con errores
        context = {
            # En la tabla mostraremos TODAS las personas y filtraremos por JS (pestañas)
            "personas": personas,
            "personas_habilitadas": personas_habilitadas,
            "personas_deshabilitadas": personas_deshabilitadas,
            "form_p": form_p,
            "form_d": form_d,
        }
        return render(request, "empresa_persona/empresa_clientes.html", context)

    # GET normal
    context = {
        "personas": personas,
        "personas_habilitadas": personas_habilitadas,
        "personas_deshabilitadas": personas_deshabilitadas,
        "form_p": EmpresaPersonaForm(),
        "form_d": DireccionForm(),
    }
    return render(request, "empresa_persona/empresa_clientes.html", context)


# ✅ EDITAR
@transaction.atomic
def editar_persona(request, pk):
    """
    Edita una EmpresaPersona existente junto con su dirección.
    El formulario se abre en el mismo modal de creación.
    """
    persona = get_object_or_404(EmpresaPersona, pk=pk)
    direccion = persona.emppe_dire

    if request.method == "POST":
        form_p = EmpresaPersonaForm(request.POST, instance=persona)
        form_d = DireccionForm(request.POST, instance=direccion)
        if form_p.is_valid() and form_d.is_valid():
            form_d.save()
            form_p.save()
            messages.success(
                request,
                f'Se ha actualizado la información de "{persona.emppe_nom}".'
            )
            return redirect("empresa_clientes")

    # En caso de error o GET forzado simplemente volvemos a la lista
    return redirect("empresa_clientes")


# ✅ INHABILITAR (antes "eliminar")
@transaction.atomic
def eliminar_persona(request, pk):
    """
    'Elimina' lógicamente una EmpresaPersona.
    En realidad NO se borra de la BD, solo se marca emppe_est = False.
    """
    persona = get_object_or_404(EmpresaPersona, pk=pk)
    if request.method == "POST":
        persona.emppe_est = False
        persona.save(update_fields=["emppe_est"])

        messages.warning(
            request,
            f'Cliente/proveedor "{persona.emppe_nom}" fue inhabilitado correctamente.'
        )
        return redirect("empresa_clientes")

    return JsonResponse({"error": "Método no permitido"}, status=405)


# ✅ HABILITAR
@transaction.atomic
def habilitar_persona(request, pk):
    """
    Habilita nuevamente una EmpresaPersona previamente inhabilitada
    (emppe_est pasa a True).
    """
    persona = get_object_or_404(EmpresaPersona, pk=pk)
    if request.method == "POST":
        persona.emppe_est = True
        persona.save(update_fields=["emppe_est"])

        messages.success(
            request,
            f'Cliente/proveedor "{persona.emppe_nom}" fue habilitado correctamente.'
        )
        return redirect("empresa_clientes")

    return JsonResponse({"error": "Método no permitido"}, status=405)


# =========================
#       OTRAS VISTAS
# =========================

def index(request):
    """Redirige al inicio de sesión si no hay sesión activa."""
    if not request.session.get("user_role"):
        return redirect("login")
    return redirect("dashboard")


def login_view(request):
    if request.session.get("user_role"):
        return redirect("dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["usuario"]
        password = form.cleaned_data["password"]

        usuario = UsuarioSistema.objects.filter(username=username).first()

        if usuario is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "login/login.html", {"form": form})

        if not usuario.is_active:
            messages.error(
                request,
                "Tu cuenta está desactivada. Contacta al administrador."
            )
            return render(request, "login/login.html", {"form": form})

        if not usuario.check_password(password):
            codigo_temporal = (
                PasswordResetCode.objects.filter(
                    user=usuario, code=password, used=False
                )
                .order_by("-created_at")
                .first()
            )

            if not (codigo_temporal and codigo_temporal.is_valid()):
                messages.error(request, "Usuario o contraseña incorrectos.")
                return render(request, "login/login.html", {"form": form})

            codigo_temporal.used = True
            codigo_temporal.save(update_fields=["used"])

        request.session["user_id"] = usuario.id
        request.session["user_role"] = usuario.role
        request.session["username"] = usuario.username

        messages.success(
            request,
            "Ingreso exitoso. Te recomendamos actualizar tu contraseña si usaste una temporal.",
        )
        return redirect("dashboard")

    return render(request, "login/login.html", {"form": form})


def dashboard(request):
    """
    Dashboard principal con:
    - Ingresos / egresos
    - IVA
    - Pagos vencidos / por vencer
    - Proyectos por estado
    - Clientes activos
    - Ingresos mensuales (para gráfico)
    """
    today = timezone.now().date()

    # Subquery: subtotal por documento
    documento_subtotal = Subquery(
        DetalleDoc.objects.filter(documento=OuterRef("pk"))
        .annotate(line_total=F("dedoc_cant") * F("producto__produ_bruto"))
        .values("documento")
        .annotate(total=Sum("line_total"))
        .values("total")[:1]
    )

    # Subquery: IVA por documento
    documento_iva = Subquery(
        DetalleDoc.objects.filter(documento=OuterRef("pk"))
        .annotate(iva_line=F("dedoc_cant") * F("producto__produ_iva"))
        .values("documento")
        .annotate(total=Sum("iva_line"))
        .values("total")[:1]
    )

    # ================================
    #      INGRESOS / EGRESOS
    # ================================
    ingresos = (
        Documento.objects.filter(transacciones__tipo__tipo_trans__iexact="ingreso")
        .annotate(subtotal=Coalesce(documento_subtotal, 0))
        .aggregate(total=Sum("subtotal"))
    )

    egresos = (
        Documento.objects.filter(transacciones__tipo__tipo_trans__iexact="egreso")
        .annotate(subtotal=Coalesce(documento_subtotal, 0))
        .aggregate(total=Sum("subtotal"))
    )

    # ================================
    #              IVA
    # ================================
    iva_totales = (
        Documento.objects.filter(transacciones__tipo__tipo_trans__iexact="ingreso")
        .annotate(iva_total=Coalesce(documento_iva, 0))
        .aggregate(total=Sum("iva_total"))
    )

    # ================================
    #   PAGOS VENCIDOS / POR VENCER
    # ================================
    pagos_vencidos = Documento.objects.filter(
        docum_fecha_ven__lt=today,
    ).exclude(docum_estado__iexact="pagado").count()

    pagos_por_vencer = Documento.objects.filter(
        docum_fecha_ven__gte=today,
        docum_fecha_ven__lte=today + timezone.timedelta(days=14),
    ).exclude(docum_estado__iexact="pagado").count()

    # ================================
    #         PROYECTOS
    # ================================
    proyectos_por_estado_qs = Proyecto.objects.values("proye_estado").annotate(
        total=Count("proye_idt")
    )
    proyecto_labels = [estado for estado, _ in Proyecto.ESTADOS]
    proyectos_por_estado = {estado: 0 for estado in proyecto_labels}

    for registro in proyectos_por_estado_qs:
        proyectos_por_estado[registro["proye_estado"]] = registro["total"]

    # ================================
    #        CLIENTES ACTIVOS
    # ================================
    clientes_activos = EmpresaPersona.objects.filter(
        emppe_est=True,
        emppe_sit__in=["cliente", "ambos"],
    ).count()

    # ================================
    #      INGRESOS MENSUALES
    # ================================
    ingresos_mensuales_raw = (
        Documento.objects.filter(transacciones__tipo__tipo_trans__iexact="ingreso")
        .annotate(month=TruncMonth("docum_fecha_emi"), subtotal=Coalesce(documento_subtotal, 0))
        .values("month")
        .annotate(total=Sum("subtotal"))
        .order_by("month")
    )

    ingresos_por_mes = {
        registro["month"].month: registro["total"]
        for registro in ingresos_mensuales_raw
        if registro["month"]
    }

    meses_labels = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ]

    ingresos_dataset = [ingresos_por_mes.get(mes, 0) for mes in range(1, 13)]

    # ================================
    #            CONTEXTO
    # ================================
    context = {
        "ingresos_total": ingresos.get("total") or 0,
        "egresos_total": egresos.get("total") or 0,
        "iva_total": iva_totales.get("total") or 0,

        "pagos_vencidos": pagos_vencidos,
        "pagos_por_vencer": pagos_por_vencer,

        "proyectos_pendientes": proyectos_por_estado.get("Pendiente", 0),
        "proyectos_en_progreso": proyectos_por_estado.get("En Progreso", 0),
        "proyectos_terminados": proyectos_por_estado.get("Terminado", 0),
        "proyectos_cancelados": proyectos_por_estado.get("Cancelado", 0),

        "clientes_activos": clientes_activos,

        "income_chart_data": {
            "labels": meses_labels,
            "totals": ingresos_dataset,
        },

        "username": request.user.username if request.user.is_authenticated else "Invitado",
    }

    return render(request, "login/dashboard.html", context)


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
