# FacturacionApp/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openpyxl
from openpyxl.styles import Font

from .models import (
    Documento, DetalleDoc, Transaccion,
    TipoTransaccion, TipoPago, FormaPago, Proyecto
)
from ProductoServicioApp.models import ProductoServicio
from .forms import DocumentoForm


# ============================================================
# CONTEXTO COMÚN DE FACTURACIÓN
# ============================================================
def _facturacion_context(doc_form):
    documentos = Documento.objects.all().order_by("-docum_num")

    # Solo documentos activos (no anulados)
    activos = documentos.exclude(docum_estado="ANULADO")

    total_docs = activos.count()
    total_pendientes = activos.filter(docum_estado="PENDIENTE").count()
    total_pagados = activos.filter(docum_estado="PAGADO").count()

    # ATRASADO es lógico, no físico
    total_atrasados = sum(1 for d in activos if d.estado_real == "ATRASADO")

    monto_total_bruto = sum(d.total for d in activos)

    # ==========================================================
    # ✅ NUEVO: SUMAR SALDO PENDIENTE SOLO DE DOCUMENTOS EGRESO
    # saldo pendiente = total (bruto) - sum(pagado_cant * precio)
    # ==========================================================
    saldo_pendiente_egresos = 0

    for d in activos:
        # 1) Determinar si es EGRESO (usa tu propiedad si existe)
        es_egreso = getattr(d, "es_egreso", None)

        # Si no existe la propiedad, lo inferimos desde la transacción
        if es_egreso is None:
            tipo_trans = (
                d.transacciones.first().tipo.tipo_trans.upper()
                if d.transacciones.exists() and d.transacciones.first().tipo
                else ""
            )
            es_egreso = "EGRESO" in tipo_trans

        if not es_egreso:
            continue

        # 2) Calcular pagado total del documento desde el detalle
        pagado_doc = 0
        for det in d.detalles.select_related("producto").all():
            precio = int(det.producto.produ_bruto) if det.producto and det.producto.produ_bruto else 0
            pagado_doc += int(det.dedoc_pagado or 0) * precio

        # 3) Saldo pendiente del documento
        total_doc = int(d.total or 0)  # total = bruto (como lo manejas tú)
        saldo = total_doc - pagado_doc

        if saldo > 0:
            saldo_pendiente_egresos += saldo


    return {
        "documentos": activos,
        "documentos_todos": documentos,

        "total_docs": total_docs,
        "total_pendientes": total_pendientes,
        "total_pagados": total_pagados,
        "total_atrasados": total_atrasados,
        "monto_total_bruto": monto_total_bruto,

        "saldo_pendiente_egresos": saldo_pendiente_egresos,

        "doc_form": doc_form,
        "tipos_trans": TipoTransaccion.objects.all(),
        "tipos_pago": TipoPago.objects.all(),
        "productos": ProductoServicio.objects.all(),

        "errores": False,
        "external_errors": {},
    }


# ============================================================
# LISTA DOCUMENTOS (ÚNICA PANTALLA)
# ============================================================

def lista_documentos(request):
    context = _facturacion_context(DocumentoForm())
    return render(request, "facturacion/facturacion.html", context)


# ============================================================
# ANULAR DOCUMENTO COMPLETO
# ============================================================
def anular_documento(request, pk):
    if request.method != "POST":
        return redirect("facturacionapp:lista_documentos")

    doc = get_object_or_404(Documento, pk=pk)

    doc.docum_estado = "ANULADO"
    doc.docum_obs = (doc.docum_obs or "") + "\nDocumento anulado."
    doc.save(update_fields=["docum_estado", "docum_obs"])

    return redirect("facturacionapp:lista_documentos")



# ============================================================
# CREAR DOCUMENTO + DETALLE (UN SOLO SUBMIT)
# ============================================================

def crear_documento(request):
    if request.method != "POST":
        return redirect("facturacionapp:lista_documentos")

    form = DocumentoForm(request.POST)

    # Campos externos
    tipo_pago_id = request.POST.get("tipo_pago")
    dias_pago = request.POST.get("fpago_dias")
    tipo_trans_id = request.POST.get("tipo_trans")
    detalle_json = request.POST.get("detalle_json")

    errores_externos = []
    external_field_errors = {}
    dias_pago_int = None

    # -------------------------------
    # Validar tipo transacción
    # -------------------------------
    if not tipo_trans_id:
        msg = "Selecciona un tipo de transacción para continuar."
        errores_externos.append(msg)
        external_field_errors.setdefault("tipo_trans", msg)

    # -------------------------------
    # Validar tipo pago
    # -------------------------------
    if not tipo_pago_id:
        msg = "Selecciona un tipo de pago para continuar."
        errores_externos.append(msg)
        external_field_errors.setdefault("tipo_pago", msg)

    # -------------------------------
    # Validar días de pago
    # -------------------------------
    if not dias_pago:
        msg = "Ingresa los días de pago para continuar."
        errores_externos.append(msg)
        external_field_errors.setdefault("fpago_dias", msg)
    else:
        try:
            dias_pago_int = int(dias_pago)
            if dias_pago_int <= 0:
                msg = "Los días de pago deben ser mayores que cero."
                errores_externos.append(msg)
                external_field_errors.setdefault("fpago_dias", msg)
        except ValueError:
            msg = "Los días de pago deben ser numéricos."
            errores_externos.append(msg)
            external_field_errors.setdefault("fpago_dias", msg)

    # -----------------------------------------------------
    # Parsear DETALLE JSON
    # -----------------------------------------------------
    try:
        detalle_data = json.loads(detalle_json) if detalle_json else []
    except json.JSONDecodeError:
        detalle_data = []
        msg = "No se pudo leer el detalle de productos. Intenta nuevamente."
        errores_externos.append(msg)
        external_field_errors.setdefault("detalle", msg)

    if not detalle_data:
        msg = "Debes agregar al menos un producto o servicio al detalle."
        errores_externos.append(msg)
        external_field_errors.setdefault("detalle", msg)

    # Validar formulario base
    form.is_valid()

    # Validaciones de fecha con vigencias
    if not form.errors:
        docum_fecha_emi = form.cleaned_data.get("docum_fecha_emi")
        docum_fecha_recl = form.cleaned_data.get("docum_fecha_recl")

        ids = [item["id"] for item in detalle_data if "id" in item]
        productos = ProductoServicio.objects.filter(pk__in=ids)
        map_prod = {str(p.pk): p for p in productos}

        for item in detalle_data:
            prod = map_prod.get(str(item["id"]))
            if not prod:
                continue

            inicio = prod.produ_vigencia_inicio
            fin = prod.produ_vigencia_fin

            # Validaciones fecha emisión / reclamo
            if docum_fecha_emi:
                if inicio and docum_fecha_emi < inicio:
                    form.add_error("docum_fecha_emi",
                        f"La emisión para {prod.produ_nom} debe ser ≥ {inicio}."
                    )
                if fin and docum_fecha_emi > fin:
                    form.add_error("docum_fecha_emi",
                        f"La emisión para {prod.produ_nom} debe ser ≤ {fin}."
                    )

            if docum_fecha_recl:
                if inicio and docum_fecha_recl < inicio:
                    form.add_error("docum_fecha_recl",
                        f"El reclamo para {prod.produ_nom} debe ser ≥ {inicio}."
                    )
                if fin and docum_fecha_recl > fin:
                    form.add_error("docum_fecha_recl",
                        f"El reclamo para {prod.produ_nom} debe ser ≤ {fin}."
                    )

    # Enviar errores externos
    for e in errores_externos:
        form.add_error(None, e)

    if form.errors:
        context = _facturacion_context(form)
        context["errores"] = True
        context["external_errors"] = external_field_errors
        return render(request, "facturacion/facturacion.html", context)

    # ===============================
    # Crear FormaPago
    # ===============================
    forma_pago = FormaPago.objects.create(
        tipo_pago_id=tipo_pago_id,
        fpago_dias=dias_pago_int,
    )

    # ===============================
    # Crear Documento
    # ===============================
    documento = form.save(commit=False)
    documento.forma_pago = forma_pago
    documento.save()

    # ===============================
    # Crear Transacción inicial
    # ===============================
    if tipo_trans_id:
        Transaccion.objects.create(
            documento=documento,
            tipo_id=tipo_trans_id,
            trans_fecha=timezone.now().date(),
            trans_monto=0,
        )

    # ===============================
    # Crear DETALLE (con pagado parcial)
    # ===============================
    for item in detalle_data:

        producto = get_object_or_404(ProductoServicio, pk=item["id"])

        cant = item["cant"]
        pagado = item.get("pagado", 0)

        # Seguridad
        if pagado < 0:
            pagado = 0
        if pagado > cant:
            pagado = cant

        DetalleDoc.objects.create(
            documento=documento,
            producto=producto,
            dedoc_cant=cant,
            dedoc_pagado=pagado,
            dedoc_obs=item.get("obs", "")
        )

    # ===============================
    # Actualizar transacción
    # ===============================
    trans = documento.transacciones.first()
    if trans:
        trans.trans_monto = documento.total
        trans.save()

    # ===============================
    # Recalcular estado según detalle
    # ===============================
    documento.save()  # aquí aplica tu lógica de estado en models.py

    return redirect("facturacionapp:lista_documentos")


# ============================================================
# API: OBTENER DATOS DEL DOCUMENTO (GET)
# ============================================================

def api_get_documento(request, pk):
    doc = get_object_or_404(Documento, pk=pk)

    # DETALLE seguro — evita errores si un producto fue eliminado
    detalles = []

    for d in doc.detalles.select_related("producto").all():
        producto = d.producto  # puede ser None

        precio = int(producto.produ_bruto) if producto and producto.produ_bruto else 0

        total_item = d.dedoc_cant * precio
        pagado_item = d.dedoc_pagado * precio
        pendiente_item = total_item - pagado_item

        detalles.append({
            # --- Identificación ---
            "id": producto.produ_id if producto else None,
            "nombre": producto.produ_nom if producto else "(Producto eliminado)",
            "detalle_id": d.pk,

            # --- Valores base ---
            "precio": precio,
            "cant": d.dedoc_cant,
            "pagado_cant": d.dedoc_pagado,

            # --- Montos (LO IMPORTANTE) ---
            "total": total_item,
            "pagado_monto": pagado_item,
            "pendiente_monto": pendiente_item,

            # --- Observaciones ---
            "obs": d.dedoc_obs,
        })

    # ============================
    # RESUMEN MONETARIO DOCUMENTO
    # ============================
    total_doc = doc.total
    pagado_total = sum(d["pagado_monto"] for d in detalles)
    pendiente_total = total_doc - pagado_total



    data = {
        "docum_num": doc.docum_num,

        "tipo_doc": doc.tipo_doc.tidoc_id if doc.tipo_doc else None,
        "tipo_doc_nombre": doc.tipo_doc.tidoc_tipo if doc.tipo_doc else "",

        "empresa": doc.empresa.emppe_id if doc.empresa else None,
        "empresa_nombre": doc.empresa.emppe_nom if doc.empresa else "(Sin cliente)",

        "proyecto": doc.proyecto.proye_idt if doc.proyecto else None,
        "proyecto_nombre": doc.proyecto.proye_desc if doc.proyecto else "",

        "tipo_trans": doc.transacciones.first().tipo_id if doc.transacciones.exists() else None,
        "tipo_trans_nombre": doc.transacciones.first().tipo.tipo_trans if doc.transacciones.exists() else "",

        "docum_estado": doc.docum_estado,

        "docum_fecha_emi": doc.docum_fecha_emi.strftime("%Y-%m-%d") if doc.docum_fecha_emi else "",
        "docum_fecha_ven": doc.docum_fecha_ven.strftime("%Y-%m-%d") if doc.docum_fecha_ven else "",
        "docum_fecha_recl": doc.docum_fecha_recl.strftime("%Y-%m-%d") if doc.docum_fecha_recl else "",

        "tipo_pago": doc.forma_pago.tipo_pago.tpago_id if doc.forma_pago else None,
        "tipo_pago_nombre": doc.forma_pago.tipo_pago.tpago_tipo if doc.forma_pago else "",
        "fpago_dias": doc.forma_pago.fpago_dias if doc.forma_pago else "",

        "resumen": {
            "total": total_doc,
            "pagado": pagado_total,
            "pendiente": pendiente_total,
        },

        "detalle": detalles,
    }

    return JsonResponse(data)

@require_POST
def api_toggle_pagado_detalle(request, doc_id):
    doc = get_object_or_404(Documento, pk=doc_id)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)

    detalle_id = payload.get("detalle_id")
    checked = bool(payload.get("checked"))

    if not detalle_id:
        return JsonResponse({"success": False, "error": "detalle_id requerido"}, status=400)

    det = get_object_or_404(DetalleDoc, pk=detalle_id, documento=doc)

    # checked => pagado total del ítem; unchecked => 0
    det.dedoc_pagado = det.dedoc_cant if checked else 0
    det.save(update_fields=["dedoc_pagado"])

    # Recalcular estado del documento (tu lógica en models.py)
    doc.save()

    return JsonResponse({"success": True})
# ============================================================
# EDITAR DOCUMENTO (POST)
# ============================================================

def editar_documento_post(request, pk):
    doc = get_object_or_404(Documento, pk=pk)

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    form = DocumentoForm(request.POST, instance=doc)
    if not form.is_valid():
        return JsonResponse(
            {"error": "Formulario inválido", "detalles": form.errors},
            status=400
        )

    # Guardar datos generales del documento
    form.save()

    # ====================================
    # FORMA DE PAGO
    # ====================================
    tipo_pago_id = request.POST.get("tipo_pago")
    fpago_dias = request.POST.get("fpago_dias", 0) or 0

    if tipo_pago_id:
        fp = doc.forma_pago
        fp.tipo_pago_id = tipo_pago_id
        fp.fpago_dias = fpago_dias
        fp.save()

    # ====================================
    # TRANSACCIÓN
    # ====================================
    tipo_trans_id = request.POST.get("tipo_trans")
    if tipo_trans_id:
        tipo_trans = TipoTransaccion.objects.get(pk=tipo_trans_id)
        Transaccion.objects.update_or_create(
            documento=doc,
            defaults={
                "tipo": tipo_trans,
            }
        )

    # ====================================
    # DETALLE (PAGADO POR ÍTEM)
    # ====================================
    lista = json.loads(request.POST.get("detalle_json", "[]"))

    # Limpiar detalle anterior
    doc.detalles.all().delete()

    for item in lista:
        producto = ProductoServicio.objects.get(pk=item["id"])

        cant = int(item.get("cant", 0))
        pagado = int(item.get("pagado", 0))

        if pagado > cant:
            pagado = cant  # seguridad

        DetalleDoc.objects.create(
            documento=doc,
            producto=producto,
            dedoc_cant=cant,
            dedoc_pagado=pagado,
            dedoc_obs=item.get("obs", ""),
        )

    # ====================================
    # ACTUALIZAR MONTO TRANSACCIÓN
    # ====================================
    trans = doc.transacciones.first()
    if trans:
        trans.trans_monto = doc.total
        trans.save()

    # ====================================
    # ACTUALIZAR ESTADO AUTOMÁTICO
    # ====================================
    doc.save()


    return redirect("facturacionapp:lista_documentos")


# ============================================================
# EXPORTAR PDF GENERAL
# ============================================================

def export_pdf_all(request):
    documentos = Documento.objects.exclude(docum_estado="ANULADO").order_by("docum_num")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = "attachment; filename=documentos.pdf"

    p = canvas.Canvas(response, pagesize=letter)
    y = 760

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Listado de documentos")
    y -= 40

    p.setFont("Helvetica", 10)

    for doc in documentos:
        if y < 120:
            p.showPage()
            y = 760
            p.setFont("Helvetica", 10)

        cliente = doc.empresa.emppe_nom if doc.empresa else "SIN CLIENTE"
        tipo_doc = doc.tipo_doc.tidoc_tipo if doc.tipo_doc else "N/A"
        fecha_emi = doc.docum_fecha_emi or "-"
        fecha_ven = doc.docum_fecha_ven or "-"

        bruto = 0
        for d in doc.detalles.all():
            if d.producto and d.producto.produ_bruto:
                bruto += (d.dedoc_cant * d.producto.produ_bruto)

        neto = round(bruto / 1.19) if bruto else 0
        iva = bruto - neto

        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, f"Documento N° {doc.docum_num}")
        y -= 16

        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Tipo: {tipo_doc}")
        y -= 14

        p.drawString(50, y, f"Cliente: {cliente}")
        y -= 14

        p.drawString(50, y, f"Emisión: {fecha_emi}     Vencimiento: {fecha_ven}")
        y -= 14

        p.drawString(50, y, f"Estado: {doc.docum_estado}")
        y -= 18

        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, f"Neto: ${neto:,}".replace(",", "."))
        y -= 14

        p.drawString(50, y, f"IVA: ${iva:,}".replace(",", "."))
        y -= 14

        p.drawString(50, y, f"Total: ${bruto:,}".replace(",", "."))
        y -= 18

        if doc.detalles.exists():
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, "Productos:")
            y -= 14

            p.setFont("Helvetica", 10)

            for det in doc.detalles.all():
                nombre_prod = det.producto.produ_nom if det.producto else "SIN PRODUCTO"
                precio = det.producto.produ_bruto if (det.producto and det.producto.produ_bruto) else 0
                subtotal = det.dedoc_cant * precio

                linea = f"- {nombre_prod} (x{det.dedoc_cant}) = ${subtotal:,}".replace(",", ".")
                p.drawString(60, y, linea)
                y -= 14

                if y < 80:
                    p.showPage()
                    y = 760
                    p.setFont("Helvetica", 10)

        y -= 10

    p.showPage()
    p.save()
    return response


# ============================================================
# EXPORTAR EXCEL GENERAL
# ============================================================

def export_excel_all(request):
    documentos = Documento.objects.all().order_by("docum_num")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Documentos"

    ws.append([
        "N° Documento",
        "Cliente",
        "Tipo Documento",
        "Estado",
        "Fecha Emisión",
        "Fecha Vencimiento",
        "Neto",
        "IVA",
        "Total",
        "Productos",
    ])

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for d in documentos:
        cliente = d.empresa.emppe_nom if d.empresa else "SIN CLIENTE"
        tipo_doc = d.tipo_doc.tidoc_tipo if d.tipo_doc else "N/A"
        fecha_emi = str(d.docum_fecha_emi or "")
        fecha_ven = str(d.docum_fecha_ven or "")

        bruto = 0
        productos_list = []

        for det in d.detalles.all():
            nombre_prod = det.producto.produ_nom if det.producto else "SIN PRODUCTO"
            precio = det.producto.produ_bruto if (det.producto and det.producto.produ_bruto) else 0
            subtotal = det.dedoc_cant * precio

            bruto += subtotal
            productos_list.append(f"{nombre_prod} (x{det.dedoc_cant})")

        neto = round(bruto / 1.19) if bruto else 0
        iva = bruto - neto
        productos = ", ".join(productos_list)

        ws.append([
            d.docum_num,
            cliente,
            tipo_doc,
            d.docum_estado,
            fecha_emi,
            fecha_ven,
            neto,
            iva,
            bruto,
            productos,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = "attachment; filename=documentos.xlsx"

    wb.save(response)
    return response



# ============================================================
# VISTA: CONTABILIDAD POR PROYECTO
# ============================================================
def api_documentos_por_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)

    documentos = Documento.objects.filter(proyecto=proyecto).select_related(
        "empresa", "tipo_doc"
    )

    # ---------------------------------------------
    # 🟩 COSTO TOTAL DEL PROYECTO (nuevo campo)
    # ---------------------------------------------
    proye_cost = proyecto.proye_cost if hasattr(proyecto, "proye_cost") else 0

    ingresos = 0
    egresos = 0

    data_docs = []

    for d in documentos:

        # Calcular MONTO BRUTO del documento
        bruto = sum(
            det.dedoc_cant * (det.producto.produ_bruto if det.producto else 0)
            for det in d.detalles.all()
        )

        # Determinar si es ingreso o egreso
        tipo_trans = (
            d.transacciones.first().tipo.tipo_trans.upper()
            if d.transacciones.exists()
            else "INGRESO"
        )

        if "INGRESO" in tipo_trans:
            ingresos += bruto
        else:
            egresos += bruto

        # Guardar documento para la tabla del modal
        data_docs.append({
            "id": d.pk,
            "num": d.docum_num,
            "fecha": d.docum_fecha_emi.strftime("%Y-%m-%d") if d.docum_fecha_emi else "",
            "estado": d.docum_estado,
            "cliente": d.empresa.emppe_nom if d.empresa else "Sin cliente",
            "total": bruto,
            "tipo_trans": tipo_trans,
        })

    # ---------------------------------------------
    # 🧮 CÁLCULO DE UTILIDAD
    # ---------------------------------------------
    utilidad = ingresos - egresos

    # ---------------------------------------------
    # 🟦 CÁLCULO DE BARRAS PARA EL FRONT
    # ---------------------------------------------
    barra_total = proye_cost

    barra_restante = max(proye_cost - egresos, 0)

    # porcentaje para llenar la barra
    if proye_cost > 0:
        barra_porcentaje = round((barra_restante / proye_cost) * 100, 2)
    else:
        barra_porcentaje = 0

    return JsonResponse({
        "success": True,
        "proyecto": {
            "id": proyecto.pk,
            "nombre": proyecto.proye_desc,
            "cliente": proyecto.cliente.emppe_nom if hasattr(proyecto, "cliente") else "",
            "proye_cost": proye_cost,
        },
        "docs": data_docs,
        "ingresos": ingresos,
        "egresos": egresos,
        "utilidad": utilidad,

        # datos para la barra de utilidad
        "barra": {
            "total": barra_total,
            "restante": barra_restante,
            "porcentaje": barra_porcentaje,
        }
    })

@csrf_exempt
def api_quitar_documento(request, doc_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"})

    doc = get_object_or_404(Documento, pk=doc_id)

    # quitar relación con proyecto
    if doc.docum_estado == "ANULADO":
        return JsonResponse({"success": False, "error": "Documento anulado"})

    doc.proyecto = None
    doc.save(update_fields=["proyecto"])

    return JsonResponse({"success": True})