# FacturacionApp/forms.py
import json

from django import forms
from django.core.exceptions import ValidationError
from EmpresaPersonaApp.models import EmpresaPersona
from ProyectoApp.models import Proyecto

from .models import Documento, DetalleDoc


# ============================================================
#   FORMULARIO PRINCIPAL (DOCUMENTO)
# ============================================================

class DocumentoForm(forms.ModelForm):
    """
    Formulario principal de Documento.
    Aquí definimos:
    - Campos adicionales/reescritos (docum_num, docum_estado)
    - Reglas de requerido
    - Validaciones de negocio en clean_docum_num y clean()
    """

    # Posibles estados del documento (para el choice del form)
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PAGADO", "Pagado"),
        ("MITAD", "Pagado Mitad"),
        ("ATRASADO", "Atrasado"),
    ]

    # ===========================
    # Campo docum_num redefinido
    # ===========================
    docum_num = forms.IntegerField(
        label="Número de documento",
        required=True,  # 🔴 Obligatorio
        error_messages={
            "required": "Debes indicar el número del documento.",
            "invalid": "Solo se permiten números en el campo de documento.",
        },
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej: 10230",
            }
        ),
        help_text="Ingresa un número único y mayor a cero.",
    )

    # ===========================
    # Campo docum_estado redefinido
    # ===========================
    docum_estado = forms.ChoiceField(
        label="Estado del documento",
        choices=ESTADOS,
        required=True,  # 🔴 Obligatorio
        error_messages={
            "required": "Selecciona el estado actual del documento.",
            "invalid_choice": "El estado seleccionado no es válido.",
        },
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Documento
        fields = [
            "docum_num",
            "tipo_doc",
            "empresa",
            "proyecto",
            "docum_estado",
            "docum_fecha_emi",
            "docum_fecha_ven",
            "docum_fecha_recl",
            "docum_obs",
        ]
        # NOTA: si quisieras, podrías mover aquí los widgets que están
        # abajo en __init__ usando Meta.widgets. Por ahora se mantienen
        # en __init__ para que veas todo junto.

    def __init__(self, *args, **kwargs):
        """
        Ajustamos:
        - Qué campos son obligatorios
        - Qué campos son opcionales
        - Widgets (clases CSS, tipo de input, etc.)
        """
        super().__init__(*args, **kwargs)

        # ============================
        # QuerySets filtrados
        # ============================
        empresa_qs = EmpresaPersona.objects.filter(emppe_est=True)
        proyecto_qs = Proyecto.objects.filter(cliente__emppe_est=True)

        # Si estamos editando y la empresa/proyecto asociado está inactivo,
        # lo agregamos para evitar errores de elección inválida, pero sin
        # permitir que aparezca para nuevos registros.
        if self.instance.pk:
            if getattr(self.instance, "empresa", None):
                empresa_qs = empresa_qs | EmpresaPersona.objects.filter(
                    pk=self.instance.empresa.pk
                )

            if getattr(self.instance, "proyecto", None):
                proyecto_qs = proyecto_qs | Proyecto.objects.filter(
                    pk=self.instance.proyecto.pk
                )

        self.fields["empresa"].queryset = empresa_qs.order_by("emppe_nom").distinct()
        self.fields["proyecto"].queryset = proyecto_qs.order_by("proye_desc").distinct()
        self.fields["tipo_doc"].queryset = (
        self.fields["tipo_doc"].queryset.order_by("tidoc_tipo")
        )

        # ============================
        # Campos que queremos OBLIGATORIOS
        # ============================
        for name in [
            "docum_num",
            "tipo_doc",
            "empresa",
            "proyecto",
            "docum_estado",
            "docum_fecha_emi",
            "docum_fecha_ven",
        ]:
            self.fields[name].required = True

        # ============================
        # Campos OPCIONALES
        # ============================
        self.fields["docum_fecha_recl"].required = False  # opcional
        self.fields["docum_obs"].required = False         # opcional

        # ============================
        # Widgets (decoración del form)
        # ============================
        self.fields["empresa"].widget = forms.Select(
            attrs={"class": "form-control select2"}
        )
        self.fields["proyecto"].widget = forms.Select(
            attrs={"class": "form-control select2"}
        )
        self.fields["tipo_doc"].widget = forms.Select(
            attrs={"class": "form-control"}
        )
        self.fields["docum_fecha_emi"].widget = forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        )
        self.fields["docum_fecha_ven"].widget = forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        )
        self.fields["docum_fecha_recl"].widget = forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        )
        self.fields["docum_obs"].widget = forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        )

    # ============================================================
    # Validación específica de docum_num
    # ============================================================
    def clean_docum_num(self):
        """
        - Debe ser > 0
        - Debe ser único (no repetido con otros documentos)
        """
        numero = self.cleaned_data.get("docum_num")

        if numero is not None and numero <= 0:
            raise ValidationError("El número de documento debe ser positivo y mayor a cero.")

        # Verificamos que no exista otro documento con el mismo número
        # (excluyendo el propio registro si estamos editando)
        existe = (
            Documento.objects
            .filter(docum_num=numero)
            .exclude(pk=self.instance.pk or None)
            .exists()
        )

        if existe:
            raise ValidationError("Ya existe un documento con este número.")

        return numero

    # ============================================================
    # Validación global del formulario
    # ============================================================
    def clean(self):
        """
        Validaciones de negocio:
        - Fechas coherentes con la vigencia del proyecto
        - Si el estado es PAGADO, debe haber detalle, etc.
        """
        cleaned_data = super().clean()

        proyecto = cleaned_data.get("proyecto")
        fecha_emi = cleaned_data.get("docum_fecha_emi")
        fecha_ven = cleaned_data.get("docum_fecha_ven")
        estado = (cleaned_data.get("docum_estado") or "").upper()

        # -------- Validaciones de fechas respecto al proyecto --------
        if proyecto and fecha_emi:
            if fecha_emi < proyecto.proye_fecha_sol:
                self.add_error(
                    "docum_fecha_emi",
                    "La fecha de emisión no puede ser anterior al inicio del proyecto.",
                )

            if proyecto.proye_fecha_ter and fecha_emi > proyecto.proye_fecha_ter:
                self.add_error(
                    "docum_fecha_emi",
                    "La fecha de emisión debe estar dentro de la vigencia del proyecto.",
                )

        if proyecto and fecha_ven:
            if fecha_ven < proyecto.proye_fecha_sol:
                self.add_error(
                    "docum_fecha_ven",
                    "La fecha de vencimiento no puede ser anterior al inicio del proyecto.",
                )

            if proyecto.proye_fecha_ter and fecha_ven > proyecto.proye_fecha_ter:
                self.add_error(
                    "docum_fecha_ven",
                    "La fecha de vencimiento debe estar dentro de la vigencia del proyecto.",
                )

        # -------- Leer detalle_json desde self.data --------
        # Aquí miramos el JSON que viene del frontend (hidden input)
        detalle_json = self.data.get("detalle_json", "[]")

        try:
            detalles = json.loads(detalle_json)
        except (TypeError, json.JSONDecodeError):
            detalles = []

        # Si es edición y no viene detalle en el POST, usamos los detalles ya asociados
        if not detalles and self.instance.pk:
            detalles = list(self.instance.detalles.all())

        # -------- Regla de negocio: no permitir PAGADO sin detalles --------
        if estado == "PAGADO" and not detalles:
            raise ValidationError(
                "No puedes marcar como pagado un documento sin detalles asociados."
            )

        return cleaned_data


# ============================================================
#   FORMULARIO DETALLE (Producto / Cantidad / Observación)
# ============================================================

class DetalleDocForm(forms.ModelForm):
    """
    Formulario para una fila de detalle del documento.
    - Producto (obligatorio si se indica cantidad u observación)
    - Cantidad (obligatoria y > 0)
    - Observación (opcional)
    """

    # Redefinimos dedoc_cant para controlar mejor errores y min_value
    dedoc_cant = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        error_messages={
            "required": "Debes indicar cuántas unidades llevará el detalle.",
            "invalid": "La cantidad solo admite números enteros.",
            "min_value": "La cantidad debe ser mayor a cero.",
        },
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )

    class Meta:
        model = DetalleDoc
        fields = ["producto", "dedoc_cant", "dedoc_obs"]
        widgets = {
            "producto": forms.Select(attrs={"class": "form-control select2"}),
            "dedoc_cant": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "dedoc_obs": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Opcional"}
            ),
        }

    def clean_dedoc_cant(self):
        """
        Aseguramos que la cantidad sea mayor a cero.
        """
        cantidad = self.cleaned_data.get("dedoc_cant")

        if cantidad is not None and cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

        return cantidad

    def clean(self):
        """
        Validación cruzada:
        - Si se indica cantidad u observación pero no se eligió producto,
          entonces error.
        """
        cleaned_data = super().clean()

        producto = cleaned_data.get("producto")
        cantidad = cleaned_data.get("dedoc_cant")
        observacion = cleaned_data.get("dedoc_obs")

        if (cantidad or observacion) and not producto:
            self.add_error("producto", "Debes seleccionar un producto para el detalle.")

        return cleaned_data


# ============================================================
#           FORMSET PARA EL DETALLE DEL DOCUMENTO
# ============================================================

# Formset por si quieres usar formularios múltiples de detalle (opcional).
DetalleFormSet = forms.modelformset_factory(
    DetalleDoc,
    form=DetalleDocForm,
    extra=1,
    can_delete=True
)
