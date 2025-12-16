# FacturacionApp/models.py
from datetime import date
from django.db import models
from EmpresaPersonaApp.models import EmpresaPersona
from ProyectoApp.models import Proyecto
from ProductoServicioApp.models import ProductoServicio


# ───────── TABLAS MAESTRAS ───────── #

class TipoTransaccion(models.Model):
    tipo_id = models.IntegerField(primary_key=True)
    tipo_trans = models.CharField(max_length=20)

    class Meta:
        db_table = "TIPO_TRANSACCION"
        managed = True

    def __str__(self):
        return self.tipo_trans


class TipoDocumento(models.Model):
    tidoc_id = models.IntegerField(primary_key=True)
    tidoc_tipo = models.CharField(max_length=20)

    class Meta:
        db_table = "TIPO_DOCUMENTO"
        managed = True

    def __str__(self):
        return self.tidoc_tipo


class TipoPago(models.Model):
    tpago_id = models.IntegerField(primary_key=True)
    tpago_tipo = models.CharField(max_length=30)

    class Meta:
        db_table = "TIPO_PAGO"
        managed = True

    def __str__(self):
        return self.tpago_tipo


# ───────── FORMA PAGO ───────── #

class FormaPago(models.Model):
    fpago_id = models.AutoField(primary_key=True)  # AUTOINCREMENT
    tipo_pago = models.ForeignKey(
        TipoPago,
        on_delete=models.PROTECT,
        db_column="TPAGO_ID"
    )
    fpago_dias = models.IntegerField(
        blank=True, null=True)

    class Meta:
        db_table = "FORMA_PAGO"

    def __str__(self):
        return f"{self.tipo_pago.tpago_tipo} - {self.fpago_dias} días"



# ───────── DOCUMENTO ───────── #
ESTADOS_DOCUMENTO = (
    ("PENDIENTE", "Pendiente"),
    ("MITAD", "Pagado Mitad"),
    ("PAGADO", "Pagado"),
    ("ANULADO", "Anulado"),
)

class Documento(models.Model):
    docum_id = models.AutoField(primary_key=True)  
    docum_num = models.IntegerField()
    docum_estado = models.CharField(
        max_length=20,
        choices=ESTADOS_DOCUMENTO,
        default="PENDIENTE"
    )

    empresa = models.ForeignKey(
        EmpresaPersona,
        on_delete=models.PROTECT,
        db_column="EMPPE_ID",
        related_name="documentos"
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column="PROYE_IDT",
        related_name="documentos",
    )
    tipo_doc = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        db_column="TIDOC_ID"
    )

    docum_fecha_emi = models.DateField()
    docum_fecha_ven = models.DateField(null=True, blank=True)
    docum_fecha_recl = models.DateField(null=True, blank=True)
    docum_obs = models.CharField(max_length=200, blank=True)

    forma_pago = models.ForeignKey(
        FormaPago,
        on_delete=models.PROTECT,
        db_column="FPAGO_ID"
    )

    class Meta:
        db_table = "DOCUMENTO"
        constraints = [
            models.UniqueConstraint(
                fields=["docum_num", "tipo_doc"],
                name="unique_docum_num_por_tipo"
            )
        ]

    def __str__(self):
        return f"{self.docum_num} - {self.tipo_doc.tidoc_tipo}"

    @property
    def total(self):
        return sum(det.subtotal() for det in self.detalles.all())

    # ===========================================
    #     EXTENSIONES PARA LEER TRANSACCIÓN
    # ===========================================

    @property
    def transaccion(self):
        """Retorna la transacción asociada (si existe)."""
        return self.transacciones.first()

    @property
    def tipo_transaccion(self):
        """Retorna 'INGRESO', 'EGRESO' o None si no hay transacción."""
        if self.transaccion:
            return self.transaccion.tipo.tipo_trans
        return None

    @property
    def es_ingreso(self):
        return self.tipo_transaccion == "INGRESO"

    @property
    def es_egreso(self):
        return self.tipo_transaccion == "EGRESO"
    
    # ===========================================

    @property
    def dias_para_vencer(self):
        """
        Calcula los días desde hoy hasta la fecha de vencimiento.
        Si está pagado o no tiene fecha → None.
        """
        if self.docum_estado.upper() in ("PAGADO", "ANULADO"):
            return None

        if not self.docum_fecha_ven:
            return None

        return (self.docum_fecha_ven - date.today()).days

    @property
    def esta_vencido(self):
        """
        True si la fecha ya pasó y el estado NO es pagado.
        """
        dias = self.dias_para_vencer
        if dias is None:
            return False
        return dias < 0

    @property
    def dias_atrasados(self):
        """
        Devuelve solo los días vencidos EN POSITIVO.
        Ej: -5 → 5
        """
        dias = self.dias_para_vencer
        if dias is None:
            return None
        if dias < 0:
            return abs(dias)
        return 0

    @property
    def estado_real(self):
        """
        Lógica inteligente:
        - Pagado → nunca cambia
        - Mitad o Pendiente vencidos → ATRASADO
        - Caso normal → estado original
        """
        estado = self.docum_estado.upper()

        if estado in ("PAGADO", "ANULADO"):
            return estado

        if self.esta_vencido:
            return "ATRASADO"

        return estado
    
    # ========== 1) Marcar todos los detalles como pagados ==========
    def marcar_todo_pagado(self):
        for det in self.detalles.all():
            det.dedoc_pagado = det.dedoc_cant
            det.save(update_fields=["dedoc_pagado"])
        self.save(recalcular_estado=True)


    # Documento.model
    def actualizar_estado_por_detalles(self):
        if self.docum_estado == "ANULADO":
            return

        detalles = self.detalles.all()
        if not detalles.exists():
            return

        total_items = sum(d.dedoc_cant for d in detalles)
        total_pagado = sum(d.dedoc_pagado for d in detalles)

        if total_pagado <= 0:
            self.docum_estado = "PENDIENTE"
        elif total_pagado >= total_items:
            self.docum_estado = "PAGADO"
        else:
            self.docum_estado = "MITAD"



    # ========== 3) SAVE con lógica automática ==========
    def save(self, *args, **kwargs):
        recalcular = kwargs.pop("recalcular_estado", True)

        super().save(*args, **kwargs)

        if recalcular:
            estado_original = self.docum_estado
            self.actualizar_estado_por_detalles()

            if self.docum_estado != estado_original:
                super().save(update_fields=["docum_estado"])

    @property
    def esta_activo(self):
        return self.docum_estado != "ANULADO"

    @property
    def estado_simple(self):
        return "activo" if self.esta_activo else "inactivo"




# ───────── DETALLE DOCUMENTO ───────── #

class DetalleDoc(models.Model):
    detalle_id = models.AutoField(primary_key=True)
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        db_column="DOCUM_ID",
        related_name="detalles"
    )
    producto = models.ForeignKey(
        ProductoServicio,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column="PRODU_ID"
    )
    dedoc_cant = models.PositiveIntegerField()
    dedoc_obs = models.CharField(max_length=200, blank=True)
    dedoc_pagado = models.PositiveIntegerField(default=0)


    class Meta:
        db_table = "DETALLE_DOC"

    def subtotal(self):
        if not self.producto:
            return 0
        return self.dedoc_cant * (self.producto.produ_bruto or 0)


# ───────── TRANSACCION ───────── #

class Transaccion(models.Model):
    trans_id = models.AutoField(primary_key=True)
    documento = models.ForeignKey(
        Documento,
        on_delete=models.PROTECT,
        db_column="DOCUM_ID",
        related_name="transacciones"
    )
    tipo = models.ForeignKey(
        TipoTransaccion,
        on_delete=models.PROTECT,
        db_column="TIPO_ID"
    )
    trans_fecha = models.DateField()
    trans_monto = models.IntegerField()

    class Meta:
        db_table = "TRANSACCION"

    def save(self, *args, **kwargs):
        self.trans_monto = self.documento.total
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo.tipo_trans} - {self.trans_monto}"


