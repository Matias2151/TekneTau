from django import forms
from .models import Direccion, Region, Ciudad, Comuna

class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = [
            'dire_calle',
            'dire_num',
            'dire_otros',
            'dire_cod_postal',
            'regi',
            'ciuda',
            'comun'
        ]
        widgets = {
            'dire_num': forms.TextInput(attrs={
                'type': 'text',               # 👉 evita el scroll de número
                'class': 'form-control',
                'placeholder': 'Ej: 742'
            }),
            'dire_calle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. Siempre Viva'
            }),
            'dire_otros': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Depto, oficina, etc.'
            }),
            'dire_cod_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 8320000'
            }),
            'regi': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_regi'
            }),
            'ciuda': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_ciuda'
            }),
            'comun': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_comun'
            }),
        }
