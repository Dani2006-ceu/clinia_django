"""Validadores reutilizados por varios modelos (no es un modelo)."""
from django.core.validators import RegexValidator

validar_dni = RegexValidator(r"^\d{8}$", "El DNI debe tener exactamente 8 dígitos.")
validar_telefono = RegexValidator(
    r"^\+?[\d\s-]{6,20}$",
    "Ingrese un teléfono válido (solo números, espacios, guiones y '+').",
)
validar_solo_letras = RegexValidator(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$", "Solo se permiten letras y espacios."
)
