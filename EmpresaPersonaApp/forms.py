# EmpresaPersonaApp/forms.py
from django import forms
from .models import EmpresaPersona
from .validacionesEmPer import (
    validar_rut_chileno,
    validar_nombre,
    validar_alias,
    validar_fono1,
    validar_fono2,
    validar_email
)

# ==============================
#   FORMULARIO EMPRESA/PERSONA
# ==============================
class EmpresaPersonaForm(forms.ModelForm):
    """Formulario de Empresa/Persona con validaciones personalizadas."""

    # 🔘 Combobox de estado
    ESTADOS = [
        (True, 'Activo'),
        (False, 'Inactivo'),
    ]

    # 🔘 Combobox de situación
    SITUACIONES = [
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('ambos', 'Cliente y Proveedor'),
    ]

    emppe_est = forms.ChoiceField(
        choices=ESTADOS,
        label="Estado",
        widget=forms.Select(attrs={
            'class': 'form-select form-control',
            'style': 'width:100%'
        })
    )

    emppe_sit = forms.ChoiceField(
        choices=SITUACIONES,
        label="Situación",
        widget=forms.Select(attrs={
            'class': 'form-select form-control',
            'style': 'width:100%'
        })
    )

    # ===============================
    #  METADATOS DEL FORMULARIO
    # ===============================
    class Meta:
        model = EmpresaPersona
        exclude = ['emppe_dire']  
        widgets = {
            'emppe_rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 76.543.210-K'
            }),
            'emppe_nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón social o nombre completo'
            }),
            'emppe_alias': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alias comercial (opcional)'
            }),
            'emppe_fono1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'emppe_fono2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono secundario (opcional)'
            }),
            'emppe_mail1': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.cl'
            }),
            'emppe_mail2': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo alternativo (opcional)'
            }),
        }

    # ===============================
    # 🧠 VALIDACIONES PERSONALIZADAS
    # ===============================

    def clean_emppe_rut(self):
        rut = self.cleaned_data.get('emppe_rut')
        validar_rut_chileno(rut)
        return rut

    def clean_emppe_nom(self):
        nombre = self.cleaned_data.get('emppe_nom')
        validar_nombre(nombre)
        return nombre

    def clean_emppe_alias(self):
        alias = self.cleaned_data.get('emppe_alias')
        if alias:  
            validar_alias(alias)
        return alias

    def clean_emppe_fono1(self):
        fono1 = self.cleaned_data.get('emppe_fono1')
        validar_fono1(fono1)
        return fono1

    def clean_emppe_fono2(self):
        fono2 = self.cleaned_data.get('emppe_fono2')
        if fono2:
            validar_fono2(fono2)
        return fono2

    def clean_emppe_mail1(self):
        mail1 = self.cleaned_data.get('emppe_mail1')
        validar_email(mail1)
        return mail1

    def clean_emppe_mail2(self):
        mail2 = self.cleaned_data.get('emppe_mail2')
        if mail2:
            validar_email(mail2)
        return mail2
