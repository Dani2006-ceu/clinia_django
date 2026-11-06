from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .Diagnostico import Diagnostico


class Tratamiento(models.Model):
    """Procedimiento indicado a partir de un diagnóstico."""

    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    FINALIZADO = "Finalizado"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_PROCESO, "En proceso"),
        (FINALIZADO, "Finalizado"),
    ]

    id = models.BigAutoField(primary_key=True)
    diagnostico = models.ForeignKey(
        Diagnostico, on_delete=models.PROTECT, related_name="tratamientos",
        verbose_name="diagnóstico",
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField("descripción del procedimiento")
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de finalización", null=True, blank=True)
    costo = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)

    class Meta:
        db_table = "tratamiento"
        ordering = ["-fecha_inicio", "-id"]
        verbose_name = "tratamiento"
        verbose_name_plural = "tratamientos"

    def __str__(self):
        return f"{self.nombre} - {self.diagnostico.cita.paciente.nombre_completo}"

    @property
    def pagado(self):
        from django.db.models import Sum
        return self.pagos.aggregate(s=Sum("monto"))["s"] or Decimal("0.00")

    @property
    def saldo(self):
        return max(self.costo - self.pagado, Decimal("0.00"))
