from django.contrib import admin

from .models import Cita, Diagnostico, Especialidad, Odontologo, Paciente, Receta, Tratamiento


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "dni", "telefono", "created_at")
    search_fields = ("nombres", "apellidos", "dni")


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado")
    list_filter = ("estado",)


@admin.register(Odontologo)
class OdontologoAdmin(admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "numero_colegiatura", "especialidad", "estado")
    list_filter = ("especialidad", "estado")
    search_fields = ("nombres", "apellidos", "numero_colegiatura")


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "paciente", "odontologo", "estado")
    list_filter = ("estado", "odontologo")
    date_hierarchy = "fecha"


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ("id", "cita", "fecha")
    date_hierarchy = "fecha"


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "diagnostico", "fecha_inicio", "costo", "estado")
    list_filter = ("estado",)


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ("medicamento", "diagnostico", "fecha_emision")
