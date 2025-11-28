# ProyectoApp/forms.py
from django import forms
from .models import Proyecto
from datetime import date
import re


class ProyectoForm(forms.ModelForm):
    """Formulario para creación y edición de proyectos (sin FK directa a cliente)."""

    # Campo opcional (referencia visual, sin relación FK)
    cliente_referencia = forms.CharField(
        label="Cliente (referencial)",
        required=False,
        widget=forms.TextInput(attrs={
            "id": "id_cliente_referencia",
            "class": "form-control",
            "placeholder": "Seleccionar cliente desde Documento...",
            "readonly": True,
        })
    )

    proye_desc = forms.CharField(
        label="Descripción del Proyecto",
        max_length=200,
        widget=forms.TextInput(attrs={
            "id": "id_proye_desc",
            "class": "form-control",
            "placeholder": "Ejemplo: Instalación de cámaras de seguridad en edificio central",
            "required": True,
        }),
        error_messages={
            "required": "Debe ingresar una descripción para el proyecto.",
        },
    )

    proye_obs = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={
            "id": "id_proye_obs",
            "class": "form-control",
            "placeholder": "Agrega observaciones o notas relevantes del proyecto...",
            "rows": 4,
        }),
    )

    proye_estado = forms.ChoiceField(
        label="Estado del Proyecto",
        choices=Proyecto.ESTADOS,
        widget=forms.Select(attrs={
            "id": "id_proye_estado",
            "class": "form-select",
            "required": True,
        }),
    )

    proye_fecha_sol = forms.DateField(
        label="Fecha de Solicitud",
        widget=forms.DateInput(attrs={
            "id": "id_proye_fecha_sol",
            "type": "date",
            "class": "form-control",
            "required": True,
        }),
    )

    proye_fecha_ter = forms.DateField(
        label="Fecha de Término",
        required=False,
        widget=forms.DateInput(attrs={
            "id": "id_proye_fecha_ter",
            "type": "date",
            "class": "form-control",
        }),
    )

    class Meta:
        model = Proyecto
        fields = [
            "proye_desc",
            "proye_obs",
            "proye_estado",
            "proye_fecha_sol",
            "proye_fecha_ter",
        ]

    # ----------------------------
    # VALIDACIONES PERSONALIZADAS
    # ----------------------------

    def clean_proye_desc(self):
        """Evita caracteres peligrosos o intentos de inyección."""
        desc = self.cleaned_data.get("proye_desc", "").strip()
        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9.,\s\-_/()]+$", desc):
            raise forms.ValidationError("La descripción contiene caracteres no permitidos.")
        return desc

    def clean_proye_obs(self):
        """Permite texto seguro en observaciones."""
        obs = self.cleaned_data.get("proye_obs", "").strip()
        if obs and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9.,\s\-_/()]*$", obs):
            raise forms.ValidationError("Las observaciones contienen caracteres no válidos.")
        return obs

    def clean(self):
        """Validaciones globales (coherencia entre fechas)."""
        cleaned_data = super().clean()
        fecha_sol = cleaned_data.get("proye_fecha_sol")
        fecha_ter = cleaned_data.get("proye_fecha_ter")

        # No permitir término antes de solicitud
        if fecha_sol and fecha_ter and fecha_ter < fecha_sol:
            self.add_error("proye_fecha_ter", "La fecha de término no puede ser anterior a la fecha de solicitud.")

        # Fecha de término opcional pero no mayor a 5 años desde hoy (protección extra)
        if fecha_ter and fecha_ter > date.today().replace(year=date.today().year + 5):
            self.add_error("proye_fecha_ter", "La fecha de término no puede superar 5 años desde hoy.")

        return cleaned_data