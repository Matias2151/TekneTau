# EmpresaPersonaApp/validacionesPersona.py
import re
from django.core.exceptions import ValidationError

# --------------------------
# ✅ VALIDAR RUT CHILENO
# --------------------------
def validar_rut_chileno(rut: str):
    """
    Valida RUT chileno (persona natural o jurídica).
    Acepta formatos con o sin puntos/guion: 12.345.678-K, 12345678-K, 12345678K
    """
    if not isinstance(rut, str):
        raise ValidationError("El RUT debe ser texto.")

    # Normalizar: quitar puntos y espacios; separar dígito verificador
    rut = rut.replace(".", "").replace(" ", "").upper()

    # Permitir con o sin guion
    if "-" in rut:
        cuerpo, dv = rut.split("-")
    else:
        if len(rut) < 2:
            raise ValidationError("RUT demasiado corto.")
        cuerpo, dv = rut[:-1], rut[-1]

    # Chequeos básicos
    if not cuerpo.isdigit():
        raise ValidationError("El cuerpo del RUT debe contener solo números.")
    # En Chile típicamente 7–8 dígitos (RUN), empresas también 7–8; admite 6–9 por seguridad
    if not (6 <= len(cuerpo) <= 9):
        raise ValidationError("El RUT no tiene un largo válido.")

    # Cálculo DV (módulo 11 con ciclo 2..7)
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1

    resto = 11 - (suma % 11)
    dv_calculado = "0" if resto == 11 else "K" if resto == 10 else str(resto)

    if dv_calculado != dv:
        raise ValidationError("Ingrese un RUT válido.")


# --------------------------
# ✅ VALIDAR NOMBRE
# --------------------------
def validar_nombre(nombre: str):
    """
    Permite solo letras (mayúsculas, minúsculas), espacios, tildes y ñ.
    """
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", nombre):
        raise ValidationError("El nombre solo puede contener letras y espacios.")


# --------------------------
# ✅ VALIDAR ALIAS
# --------------------------
def validar_alias(alias: str):
    """
    Permite letras, números y espacios. Puede ser null.
    """
    if alias and not re.match(r"^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s]*$", alias):
        raise ValidationError("El alias solo puede contener letras y números.")


# --------------------------
# ✅ VALIDAR TELÉFONOS
# --------------------------
def validar_fono1(fono1: str):
    """
    Debe comenzar con +56 y tener 9 dígitos después.
    """
    if not re.match(r"^\+56\d{9}$", fono1):
        raise ValidationError("Fono1 debe tener formato +569XXXXXXXX.")


def validar_fono2(fono2: str):
    """
    Puede contener números y símbolo +, sin letras.
    """
    if fono2 and not re.match(r"^[\d\+]+$", fono2):
        raise ValidationError("Fono2 solo puede contener números y el símbolo +.")


# --------------------------
# ✅ VALIDAR EMAILS
# --------------------------
def validar_email(email: str):
    """
    Valida formato básico y dominios comunes.
    """
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.(cl|com|org|net|edu|gov|co|io|us|es|[a-z]{2,})$", email):
        raise ValidationError("Correo electrónico inválido o con dominio no permitido.")
