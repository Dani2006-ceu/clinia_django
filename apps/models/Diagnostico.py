from django.db import models

from .Cita import Cita


class Diagnostico(models.Model):
    """Resultado clínico de una cita."""

    id = models.BigAutoField(primary_key=True)
    cita = models.ForeignKey(Cita, on_delete=models.PROTECT, related_name="diagnosticos")
    descripcion = models.TextField("diagnóstico clínico")
    recomendaciones = models.TextField(blank=True)
    fecha = models.DateField()

    class Meta:
        db_table = "diagnostico"
        ordering = ["-fecha", "-id"]
        verbose_name = "diagnóstico"
        verbose_name_plural = "diagnósticos"

    def __str__(self):
        resumen = self.descripcion[:40] + ("…" if len(self.descripcion) > 40 else "")
        return f"#{self.id} {self.cita.paciente.nombre_completo} - {resumen}"
