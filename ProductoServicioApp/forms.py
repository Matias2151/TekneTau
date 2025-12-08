# ProductoServicioApp/forms.py
from django import forms
from .models import ProductoServicio, Abastecimiento
from EmpresaPersonaApp.models import EmpresaPersona
import re


class ProductoServicioForm(forms.ModelForm):
    # 🔹 Selector de proveedor (OBLIGATORIO)
    empresa = forms.ModelChoiceField(
        queryset=EmpresaPersona.objects.filter(
            emppe_est=True,
            emppe_sit__in=['proveedor', 'ambos']
        ),
        label="Proveedor",
        required=True,
        error_messages={
            "required": "Debes seleccionar un proveedor. Este dato es obligatorio."
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estos campos SON opcionales:
        self.fields['produ_desc'].required = False
        self.fields['produ_vigencia_inicio'].required = False
        self.fields['produ_vigencia_fin'].required = False

        # 🔹 Mensajes personalizados para los campos obligatorios
        self.fields['produ_nom'].error_messages["required"] = (
            "El nombre del producto/servicio es obligatorio."
        )
        self.fields['produ_bruto'].error_messages["required"] = (
            "El valor bruto es obligatorio."
        )

    class Meta:
        model = ProductoServicio
        fields = [
            'produ_sku',
            'produ_nom',
            'produ_desc',
            'produ_bruto',
            'produ_dscto',
            'produ_vigencia_inicio',
            'produ_vigencia_fin',
            'empresa'
        ]
        labels = {
            'produ_sku': 'SKU',
            'produ_nom': 'Nombre',
            'produ_desc': 'Descripción',
            'produ_bruto': 'Valor Bruto',
            'produ_dscto': 'Descuento (%)',
            'produ_vigencia_inicio': 'Vigencia desde',
            'produ_vigencia_fin': 'Vigencia hasta',
            'empresa': 'Proveedor asociado',
        }
        widgets = {
            'produ_vigencia_inicio': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'produ_vigencia_fin': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }

    # --- Validaciones personalizadas ---
    def clean_produ_nom(self):
        nombre = (self.cleaned_data.get('produ_nom') or '').strip()

        # Si viene vacío, dejamos que salte el error "required" del campo
        if not nombre:
            raise forms.ValidationError(
                "El nombre del producto/servicio es obligatorio."
            )

        if not re.match(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ .]+$', nombre):
            raise forms.ValidationError(
                "El nombre solo puede contener letras, números, espacios y puntos."
            )
        return nombre

    def clean_produ_desc(self):
        desc = self.cleaned_data.get('produ_desc', '')
        desc = (desc or '').strip()

        # Opcional
        if not desc:
            return ''

        if not re.match(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ .]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números, espacios y puntos."
            )
        return desc

    def clean_produ_bruto(self):
        bruto = self.cleaned_data.get('produ_bruto')

        # 👉 Mensaje claro de obligatorio
        if bruto in (None, ''):
            raise forms.ValidationError("El valor bruto es obligatorio.")

        try:
            if int(bruto) <= 0:
                raise forms.ValidationError(
                    "El valor bruto debe ser un número positivo."
                )
        except (TypeError, ValueError):
            raise forms.ValidationError(
                "El valor bruto debe ser un número positivo."
            )

        return bruto

    def clean_produ_dscto(self):
        dscto = self.cleaned_data.get('produ_dscto')
        if dscto in (None, ''):
            return 0
        try:
            dscto_int = int(dscto)
        except (ValueError, TypeError):
            raise forms.ValidationError("El descuento solo puede contener números enteros.")
        if not (0 <= dscto_int <= 100):
            raise forms.ValidationError("El descuento debe estar entre 0 y 100%.")
        return dscto_int

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('produ_vigencia_inicio')
        fin = cleaned_data.get('produ_vigencia_fin')

        if inicio and fin and fin < inicio:
            self.add_error(
                'produ_vigencia_fin',
                "La fecha final debe ser posterior o igual a la fecha de inicio."
            )

        return cleaned_data

    # --- Guardado personalizado ---
    def save(self, commit=True):
        """
        Guarda el producto y crea la relación automática con EmpresaPersona
        mediante la tabla intermedia 'Abastecimiento'.
        """
        producto = super().save(commit=commit)
        empresa = self.cleaned_data.get('empresa')

        if commit and empresa:
            Abastecimiento.objects.get_or_create(emppe=empresa, produ=producto)

        return producto
