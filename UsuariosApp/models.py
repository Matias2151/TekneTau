from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class UsuarioSistema(models.Model):
    ROLE_CHOICES = (
        ("admin", "Administrador"),
        ("contador", "Contador"),
    )

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    password_visible = models.CharField(
        max_length=128,
        help_text="Almacena la contraseña en texto plano para visualización del administrador.",
    )
    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        help_text="Correo asociado al usuario para recuperación de contraseña.",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="contador")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "USUARIO_SISTEMA"
        verbose_name = "Usuario de sistema"
        verbose_name_plural = "Usuarios de sistema"

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return self.username

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)
        self.password_visible = raw_password

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        UsuarioSistema, on_delete=models.CASCADE, related_name="reset_codes"
    )
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "PASSWORD_RESET_CODE"
        verbose_name = "Código de recuperación"
        verbose_name_plural = "Códigos de recuperación"
        get_latest_by = "created_at"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - representación simple
        return f"Código {self.code} para {self.user.username}"

    def is_valid(self, minutes_valid: int = 15) -> bool:
        if self.used:
            return False
        expiry_time = self.created_at + timezone.timedelta(minutes=minutes_valid)
        return timezone.now() <= expiry_time