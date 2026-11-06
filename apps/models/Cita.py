from django.db import models

from .Odontologo import Odontologo
from .Paciente import Paciente


class Cita(models.Model):
    """Reserva de atención de un paciente con un odontólogo."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    ATENDIDA = "Atendida"
    CANCELADA = "Cancelada"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (CONFIRMADA, "Confirmada"),
        (ATENDIDA, "Atendida"),
        (CANCELADA, "Cancelada"),
    ]

    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    odontologo = models.ForeignKey(
        Odontologo, on_delete=models.PROTECT, related_name="citas", verbose_name="odontólogo"
    )
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "cita"
        ordering = ["-fecha", "-hora"]
        verbose_name = "cita"
        verbose_name_plural = "citas"
        indexes = [models.Index(fields=["fecha", "odontologo"])]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} {self.hora:%H:%M} - {self.paciente.nombre_completo}"
