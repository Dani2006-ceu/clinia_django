from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Insumo(models.Model):
    """Material o insumo del inventario del consultorio."""

    CATEGORIAS = [(c, c) for c in ("Material de restauración", "Anestesia", "Instrumental",
                                    "Bioseguridad", "Endodoncia", "Ortodoncia",
                                    "Medicamento", "Limpieza", "Otro")]
    UNIDADES = [(u, u) for u in ("Unidad", "Caja", "Frasco", "Paquete", "Jeringa", "Litro")]

    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField("código", max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    categoria = models.CharField("categoría", max_length=40, choices=CATEGORIAS)
    unidad = models.CharField(max_length=20, choices=UNIDADES, default="Unidad")
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField("stock mínimo", default=5)
    precio = models.DecimalField(
        "precio unitario", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"),
    )
    fecha_vencimiento = models.DateField("fecha de vencimiento", null=True, blank=True)

    class Meta:
        db_table = "insumo"
        ordering = ["nombre"]
        verbose_name = "insumo"
        verbose_name_plural = "insumos"

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def estado(self):
        if self.stock == 0:
            return "Agotado"
        if self.stock <= self.stock_minimo:
            return "Stock bajo"
        return "Disponible"
