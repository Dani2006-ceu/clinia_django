from django.db import models

from .Diagnostico import Diagnostico


class Receta(models.Model):
    """Prescripción de un medicamento asociada a un diagnóstico."""

    id = models.BigAutoField(primary_key=True)
    diagnostico = models.ForeignKey(
        Diagnostico, on_delete=models.PROTECT, related_name="recetas",
        verbose_name="diagnóstico",
    )
    medicamento = models.CharField(max_length=150)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    duracion = models.CharField("duración", max_length=100)
    indicaciones = models.TextField(blank=True)
    fecha_emision = models.DateField("fecha de emisión")

    class Meta:
        db_table = "receta"
        ordering = ["-fecha_emision", "-id"]
        verbose_name = "receta"
        verbose_name_plural = "recetas"

    def __str__(self):
        return f"{self.medicamento} - {self.diagnostico.cita.paciente.nombre_completo}"
