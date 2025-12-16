# ProyectoApp/forms.py
from django import forms
from .models import Proyecto
from datetime import date
import re


class ProyectoForm(forms.ModelForm):

    # --- NUEVO CAMPO: ID Proyecto público ---
    proye_idp = forms.CharField(
        label="ID Público del Proyecto",
        max_length=20,
        required=True,  # <-- Recomendado
        widget=forms.TextInput(attrs={
            "id": "id_proye_idp",
            "class": "form-control",
            "placeholder": "Ej: PROY-2025-001",
        }),
        error_messages={
            "required": "Debe ingresar un código identificador para el proyecto.",
            "unique": "Este ID ya existe, ingrese uno diferente.",
        }
    )

    # Campo referencial
    cliente_referencia = forms.CharField(
        label="Cliente (referencia)",
        required=False,
        widget=forms.TextInput(attrs={
            "id": "id_cliente_referencia",
            "class": "form-control",
            "placeholder": "Seleccionado desde Facturación...",
            "readonly": True,
        })
    )

    proye_desc = forms.CharField(
        label="Descripción del Proyecto",
        max_length=200,
        widget=forms.TextInput(attrs={
            "id": "id_proye_desc",
            "class": "form-control",
            "placeholder": "Ej: Instalación de cámaras CCTV",
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
            "placeholder": "Observaciones adicionales...",
            "rows": 4,
        }),
    )

    proye_estado = forms.ChoiceField(
        label="Estado del Proyecto",
        choices=Proyecto.ESTADOS,
        widget=forms.Select(attrs={
            "id": "id_proye_estado",
            "class": "form-select",
        }),
        error_messages={
            "required": "Debe seleccionar un estado.",
        },
    )

    proye_fecha_sol = forms.DateField(
        label="Fecha de Solicitud",
        widget=forms.DateInput(attrs={
            "id": "id_proye_fecha_sol",
            "type": "date",
            "class": "form-control",
        }),
        error_messages={
            "required": "La fecha de solicitud es obligatoria.",
        },
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
            "proye_idp",
            "proye_desc",
            "proye_obs",
            "proye_cost",
            "proye_estado",
            "proye_fecha_sol",
            "proye_fecha_ter",
        ]

    # ----------------------------
    # VALIDACIONES
    # ----------------------------

    def clean_proye_idp(self):
        pid = self.cleaned_data.get("proye_idp", "").strip()

        if not re.match(r"^[A-Za-z0-9\-_]+$", pid):
            raise forms.ValidationError(
                "El ID solo puede contener letras, números, guiones y guiones bajos."
            )

        # unicidad
        qs = Proyecto.objects.filter(proye_idp=pid)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Este ID ya está registrado.")

        return pid

    def clean_proye_desc(self):
        desc = self.cleaned_data.get("proye_desc", "").strip()
        if not desc:
            raise forms.ValidationError("Debe ingresar una descripción para el proyecto.")
        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9.,\s\-_/()]+$", desc):
            raise forms.ValidationError("La descripción contiene caracteres no permitidos.")
        return desc

    def clean_proye_obs(self):
        obs = self.cleaned_data.get("proye_obs", "").strip()
        if obs and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9.,\s\-_/()]*$", obs):
            raise forms.ValidationError("Las observaciones contienen caracteres no válidos.")
        return obs

    def clean(self):
        cleaned = super().clean()
        fecha_sol = cleaned.get("proye_fecha_sol")
        fecha_ter = cleaned.get("proye_fecha_ter")

        if fecha_sol and fecha_ter and fecha_ter < fecha_sol:
            self.add_error("proye_fecha_ter", "La fecha de término no puede ser anterior a la de solicitud.")

        hoy = date.today()
        if fecha_ter and fecha_ter > hoy.replace(year=hoy.year + 5):
            self.add_error("proye_fecha_ter", "La fecha de término no puede superar los 5 años desde hoy.")

        return cleaned
