# FacturacionApp/forms.py
from django import forms
from django.db.models import Q
from EmpresaPersonaApp.models import EmpresaPersona
from ProyectoApp.models import Proyecto
from .models import Documento, DetalleDoc


# ============================================================
#   FORMULARIO PRINCIPAL (DOCUMENTO)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_messages = {
            "docum_num": "Ingresa el número de documento para continuar.",
            "docum_estado": "Selecciona el estado del documento.",
            "tipo_doc": "Selecciona el tipo de documento.",
            "docum_fecha_emi": "La fecha de emisión es obligatoria.",
        }

        for field_name, message in required_messages.items():
            if field_name in self.fields:
                self.fields[field_name].error_messages["required"] = message

        if "empresa" in self.fields:
            empresa_qs = EmpresaPersona.objects.filter(
                emppe_est=True,
                emppe_sit__in=["cliente", "ambos"],
            )
            if getattr(self.instance, "empresa", None):
                empresa_qs = empresa_qs | EmpresaPersona.objects.filter(pk=self.instance.empresa.pk)
            self.fields["empresa"].queryset = empresa_qs.distinct().order_by("emppe_nom")

        if "proyecto" in self.fields:
            proyecto_qs = Proyecto.objects.filter(
                Q(cliente__emppe_est=True) | Q(cliente__isnull=True)
            )
            if getattr(self.instance, "proyecto", None):
                proyecto_qs = proyecto_qs | Proyecto.objects.filter(pk=self.instance.proyecto.pk)
            self.fields["proyecto"].queryset = proyecto_qs.distinct().order_by("proye_desc")

        # Campos opcionales para el formulario
        for optional_field in ["docum_fecha_recl", "docum_obs", "docum_fecha_ven"]:
            if optional_field in self.fields:
                self.fields[optional_field].required = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_messages = {
            "docum_num": "Ingresa el número de documento para continuar.",
            "docum_estado": "Selecciona el estado del documento.",
            "tipo_doc": "Selecciona el tipo de documento.",
            "docum_fecha_emi": "La fecha de emisión es obligatoria.",
        }

        for field_name, message in required_messages.items():
            if field_name in self.fields:
                self.fields[field_name].error_messages["required"] = message

        # Campos opcionales para el formulario
        for optional_field in ["docum_fecha_recl", "docum_obs", "docum_fecha_ven"]:
            if optional_field in self.fields:
                self.fields[optional_field].required = False

    class Meta:
        model = Documento

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
# ============================================================

class DetalleDocForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_messages = {
            "producto": "Selecciona un producto para el detalle.",
            "dedoc_cant": "Ingresa la cantidad para el producto.",
        }

        for field_name, message in required_messages.items():
            if field_name in self.fields:
                self.fields[field_name].error_messages["required"] = message

        if "producto" in self.fields:
            self.fields["producto"].required = True
        if "dedoc_obs" in self.fields:
            self.fields["dedoc_obs"].required = False

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
