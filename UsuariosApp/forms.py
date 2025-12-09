from django import forms
from .models import UsuarioSistema


class LoginForm(forms.Form):
    usuario = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class UsuarioSistemaForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = UsuarioSistema
        fields = ["username", "email", "password", "role", "is_active"]
        labels = {
            "username": "Nombre de usuario",
            "email": "Correo electrónico",
            "role": "Rol",
            "is_active": "Activo",
        }

    # 🔹 Validación para evitar usuarios repetidos
    def clean_username(self):
        username = self.cleaned_data["username"]
        if UsuarioSistema.objects.filter(username=username).exists():
            raise forms.ValidationError("Ya existe un usuario con ese nombre.")
        return username

    # 🔹 (Opcional) Valida correos repetidos
    def clean_email(self):
        email = self.cleaned_data["email"]
        if UsuarioSistema.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def save(self, commit=True):  # type: ignore[override]
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class ActualizarRolForm(forms.ModelForm):
    class Meta:
        model = UsuarioSistema
        fields = ["role", "is_active"]


class ActualizarPasswordForm(forms.Form):
    password = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    confirmar = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar = cleaned_data.get("confirmar")
        if password and confirmar and password != confirmar:
            self.add_error("confirmar", "Las contraseñas no coinciden.")
        return cleaned_data


class SolicitarRecuperacionForm(forms.Form):
    usuario = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Tu usuario"}),
    )

    def clean_usuario(self):
        usuario = self.cleaned_data["usuario"]
        try:
            self.user = UsuarioSistema.objects.get(username=usuario, is_active=True)
        except UsuarioSistema.DoesNotExist:
            raise forms.ValidationError("No existe un usuario activo con ese nombre.")

        if not self.user.email:
            raise forms.ValidationError("Este usuario no tiene un correo asociado.")
        return usuario


class VerificarCodigoForm(forms.Form):
    usuario = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Tu usuario"}),
    )
    codigo = forms.CharField(
        label="Código recibido",
        max_length=10,
        widget=forms.TextInput(attrs={"placeholder": "Código de un solo uso"}),
    )
    nueva_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Nueva contraseña"}),
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repite la nueva contraseña"}),
    )

    def clean(self):
        cleaned = super().clean()
        nueva = cleaned.get("nueva_password")
        confirmar = cleaned.get("confirmar_password")
        if nueva and confirmar and nueva != confirmar:
            self.add_error("confirmar_password", "Las contraseñas no coinciden.")
        return cleaned
