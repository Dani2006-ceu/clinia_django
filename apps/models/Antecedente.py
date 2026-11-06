from django.db import models

from .Paciente import Paciente


class Antecedente(models.Model):
    """Historia médica del paciente (anamnesis). Un registro por paciente."""

    id = models.BigAutoField(primary_key=True)
    paciente = models.OneToOneField(
        Paciente, on_delete=models.CASCADE, related_name="antecedente",
    )
    alergias = models.TextField(blank=True, help_text="Medicamentos, látex, anestesia, alimentos…")
    enfermedades = models.TextField(
        "enfermedades crónicas", blank=True,
        help_text="Diabetes, hipertensión, cardiopatías, hepatitis…",
    )
    medicamentos = models.TextField("medicamentos actuales", blank=True)
    cirugias = models.TextField("cirugías previas", blank=True)
    embarazo = models.BooleanField("embarazo o lactancia", default=False)
    fuma = models.BooleanField("fuma", default=False)
    observaciones = models.TextField(blank=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        db_table = "antecedente"
        ordering = ["paciente__apellidos"]
        verbose_name = "antecedente médico"
        verbose_name_plural = "antecedentes médicos"

    def __str__(self):
        return f"Antecedentes de {self.paciente.nombre_completo}"

    @property
    def tiene_alertas(self):
        return bool(self.alergias.strip() or self.enfermedades.strip() or self.embarazo)
