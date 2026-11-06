from datetime import date

from django.db import models

from ..validadores import validar_dni, validar_solo_letras, validar_telefono


class Paciente(models.Model):
    """Persona atendida en el consultorio."""

    id = models.BigAutoField(primary_key=True)
    nombres = models.CharField(max_length=100, validators=[validar_solo_letras])
    apellidos = models.CharField(max_length=100, validators=[validar_solo_letras])
    dni = models.CharField("DNI", max_length=8, unique=True, validators=[validar_dni])
    fecha_nacimiento = models.DateField("fecha de nacimiento")
    telefono = models.CharField("teléfono", max_length=20, validators=[validar_telefono])
    direccion = models.CharField("dirección", max_length=200)
    correo = models.EmailField(blank=True)
    created_at = models.DateTimeField("fecha de registro", auto_now_add=True)

    class Meta:
        db_table = "paciente"
        ordering = ["apellidos", "nombres"]
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.dni})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def edad(self):
        hoy = date.today()
        n = self.fecha_nacimiento
        return hoy.year - n.year - ((hoy.month, hoy.day) < (n.month, n.day))

    @property
    def whatsapp(self):
        """Número en formato internacional para enlaces wa.me (Perú: +51)."""
        digitos = "".join(c for c in self.telefono if c.isdigit())
        return f"51{digitos}" if len(digitos) == 9 else digitos
