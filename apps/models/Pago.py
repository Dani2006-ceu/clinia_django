from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .Tratamiento import Tratamiento


class Pago(models.Model):
    """Cobro registrado en caja a cuenta de un tratamiento."""

    METODOS = [(m, m) for m in ("Efectivo", "Tarjeta", "Yape / Plin", "Transferencia")]
    COMPROBANTES = [(c, c) for c in ("Boleta", "Factura", "Recibo interno")]

    id = models.BigAutoField(primary_key=True)
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.PROTECT, related_name="pagos")
    fecha = models.DateField("fecha de pago")
    monto = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    metodo = models.CharField("método de pago", max_length=20, choices=METODOS, default="Efectivo")
    comprobante = models.CharField(max_length=20, choices=COMPROBANTES, default="Boleta")
    numero_comprobante = models.CharField("n.º de comprobante", max_length=30, blank=True)
    observacion = models.CharField("observación", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pago"
        ordering = ["-fecha", "-id"]
        verbose_name = "pago"
        verbose_name_plural = "pagos"

    def __str__(self):
        return f"S/ {self.monto} - {self.tratamiento.nombre}"
