from django.db import models


class Especialidad(models.Model):
    """Rama de la odontología (Ortodoncia, Endodoncia, etc.)."""

    ACTIVA = "Activa"
    INACTIVA = "Inactiva"
    ESTADOS = [(ACTIVA, "Activa"), (INACTIVA, "Inactiva")]

    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ACTIVA)

    class Meta:
        db_table = "especialidad"
        ordering = ["nombre"]
        verbose_name = "especialidad"
        verbose_name_plural = "especialidades"

    def __str__(self):
        return self.nombre
