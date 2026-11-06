"""Modelos de negocio, cada uno en su propio archivo.

Los siete del enunciado (Paciente ... Receta) más los módulos complementarios
de un consultorio completo: antecedentes médicos, odontograma, caja e inventario.
"""
from .Paciente import Paciente
from .Especialidad import Especialidad
from .Odontologo import Odontologo
from .Cita import Cita
from .Diagnostico import Diagnostico
from .Tratamiento import Tratamiento
from .Receta import Receta
from .Antecedente import Antecedente
from .PiezaDental import PiezaDental
from .Pago import Pago
from .Insumo import Insumo

__all__ = [
    "Paciente", "Especialidad", "Odontologo", "Cita", "Diagnostico", "Tratamiento",
    "Receta", "Antecedente", "PiezaDental", "Pago", "Insumo",
]
