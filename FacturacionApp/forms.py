# FacturacionApp/forms.py
from django import forms
from .models import Documento, DetalleDoc


# ============================================================
#   FORMULARIO PRINCIPAL (DOCUMENTO)
#   * NO incluye forma_pago (la creamos manualmente en views)
#   * Compatible con pop-up único Datos + Detalle
# ============================================================

class DocumentoForm(forms.ModelForm):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PAGADO", "Pagado"),
        ("MITAD", "Pagado Mitad"),
        ("ATRASADO", "Atrasado"),
    ]

    docum_num = forms.IntegerField(
        label="Número de documento",
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej: 10230",
            }
        )
    )

    docum_estado = forms.ChoiceField(
        label="Estado del documento",
        choices=ESTADOS,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Documento

        # IMPORTANTE: forma_pago se quita (la creamos en views)
        fields = [
            "docum_num",
            "docum_estado",
            "empresa",
            "proyecto",
            "tipo_doc",
            "docum_fecha_emi",
            "docum_fecha_ven",
            "docum_fecha_recl",
            "docum_obs",
        ]

        widgets = {

            "empresa": forms.Select(attrs={"class": "form-control select2"}),
            "proyecto": forms.Select(attrs={"class": "form-control select2"}),

            "tipo_doc": forms.Select(attrs={"class": "form-control"}),

            "docum_fecha_emi": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "docum_fecha_ven": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "docum_fecha_recl": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),

            "docum_obs": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


# ============================================================
#   FORMULARIO DETALLE (Producto / Cant / Obs)
#   * Solo se usa en modo “añadir productos de a uno” (fallback)
#   * NO SE USA cuando enviamos detalle_json desde el pop-up
# ============================================================

class DetalleDocForm(forms.ModelForm):
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


# ============================================================
#   FORMSET (si en algún momento quieres volver a usarlo)
# ============================================================

DetalleFormSet = forms.modelformset_factory(
    DetalleDoc,
    form=DetalleDocForm,
    extra=1,
    can_delete=True
)
