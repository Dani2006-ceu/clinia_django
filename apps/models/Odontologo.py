from django.db import models

from .Especialidad import Especialidad
from ..validadores import validar_solo_letras, validar_telefono


class Odontologo(models.Model):
    """Profesional que atiende las citas."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    ESTADOS = [(ACTIVO, "Activo"), (INACTIVO, "Inactivo")]

    id = models.BigAutoField(primary_key=True)
    nombres = models.CharField(max_length=100, validators=[validar_solo_letras])
    apellidos = models.CharField(max_length=100, validators=[validar_solo_letras])
    numero_colegiatura = models.CharField("N.º de colegiatura (COP)", max_length=30, unique=True)
    telefono = models.CharField("teléfono", max_length=20, validators=[validar_telefono])
    correo = models.EmailField(blank=True)
    especialidad = models.ForeignKey(
        Especialidad, on_delete=models.PROTECT, related_name="odontologos"
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ACTIVO)

    class Meta:
        db_table = "odontologo"
        ordering = ["apellidos", "nombres"]
        verbose_name = "odontólogo"
        verbose_name_plural = "odontólogos"

    def __str__(self):
        return f"Dr(a). {self.nombres} {self.apellidos}"
