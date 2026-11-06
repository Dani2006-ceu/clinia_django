from django.db import models

from .Paciente import Paciente

# Numeración FDI de la dentadura permanente, en el orden en que se dibuja el odontograma
SUPERIOR = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
INFERIOR = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]


class PiezaDental(models.Model):
    """Estado actual de una pieza dental del paciente (odontograma)."""

    SANO = "Sano"
    CARIES = "Caries"
    OBTURADO = "Obturado"
    ENDODONCIA = "Endodoncia"
    CORONA = "Corona"
    IMPLANTE = "Implante"
    EXTRACCION = "Extracción indicada"
    AUSENTE = "Ausente"
    ESTADOS = [(e, e) for e in (SANO, CARIES, OBTURADO, ENDODONCIA, CORONA,
                                 IMPLANTE, EXTRACCION, AUSENTE)]
    PIEZAS = [(n, str(n)) for n in SUPERIOR + INFERIOR]

    id = models.BigAutoField(primary_key=True)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="piezas")
    pieza = models.PositiveSmallIntegerField(choices=PIEZAS)
    estado = models.CharField(max_length=25, choices=ESTADOS, default=SANO)
    caras = models.CharField(
        "caras afectadas", max_length=20, blank=True,
        help_text="V vestibular, L lingual, M mesial, D distal, O oclusal",
    )
    observacion = models.CharField("observación", max_length=200, blank=True)
    fecha = models.DateField("fecha de registro", auto_now=True)

    class Meta:
        db_table = "pieza_dental"
        ordering = ["paciente", "pieza"]
        unique_together = [("paciente", "pieza")]
        verbose_name = "pieza dental"
        verbose_name_plural = "odontograma"

    def __str__(self):
        return f"Pieza {self.pieza} - {self.estado}"
