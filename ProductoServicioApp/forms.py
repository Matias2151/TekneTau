# ProductoServicioApp/forms.py
from django import forms
from .models import ProductoServicio, Abastecimiento
from EmpresaPersonaApp.models import EmpresaPersona
import re


class ProductoServicioForm(forms.ModelForm):
    # 🔹 Selector de proveedor
    empresa = forms.ModelChoiceField(
        queryset=EmpresaPersona.objects.filter(
            emppe_est=True,
            emppe_sit__in=['proveedor', 'ambos']
        ),
        label="Proveedor",
        required=True
    )

    class Meta:
        model = ProductoServicio
        fields = [
            'produ_nom',
            'produ_desc',
            'produ_bruto',
            'produ_dscto',
            'empresa'
        ]
        labels = {
            'produ_nom': 'Nombre',
            'produ_desc': 'Descripción',
            'produ_bruto': 'Valor Bruto',
            'produ_dscto': 'Descuento (%)',
            'empresa': 'Proveedor asociado',
        }

    # --- Validaciones personalizadas ---
    def clean_produ_nom(self):
        nombre = self.cleaned_data.get('produ_nom', '').strip()
        if not re.match(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ .]+$', nombre):
            raise forms.ValidationError(
                "El nombre solo puede contener letras, números, espacios y puntos."
            )
        return nombre

    def clean_produ_desc(self):
        desc = self.cleaned_data.get('produ_desc', '').strip()
        if not re.match(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ .]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números, espacios y puntos."
            )
        return desc

    def clean_produ_bruto(self):
        bruto = self.cleaned_data.get('produ_bruto')
        if bruto is None or bruto <= 0:
            raise forms.ValidationError("El valor bruto debe ser un número positivo.")
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
