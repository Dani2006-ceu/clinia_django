from django.apps import AppConfig
from django.db.models.signals import post_migrate

# Permisos por puesto de trabajo: modelo -> acciones permitidas
# (view = ver/listar, add = registrar, change = editar, delete = eliminar)
TODOS = ["view", "add", "change", "delete"]
ROLES = {
    "Administrador": {
        m: TODOS for m in ["paciente", "especialidad", "odontologo", "cita",
                           "diagnostico", "tratamiento", "receta",
                           "antecedente", "piezadental", "pago", "insumo"]
    },
    "Odontologo": {
        "paciente": ["view"],
        "especialidad": ["view"],
        "odontologo": ["view"],
        "cita": ["view", "change"],
        "diagnostico": TODOS,
        "tratamiento": TODOS,
        "receta": TODOS,
        "antecedente": TODOS,
        "piezadental": TODOS,
        "pago": ["view"],
        "insumo": ["view", "change"],
    },
    # Recepción no ve información clínica (diagnósticos, tratamientos, recetas).
    "Recepcionista": {
        "paciente": ["view", "add", "change"],
        "especialidad": ["view"],
        "odontologo": ["view"],
        "cita": TODOS,
        "pago": ["view", "add"],
        "insumo": ["view"],
    },
}
ROL_POR_DEFECTO = "Recepcionista"


def crear_roles(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission

    for nombre, modelos in ROLES.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        codenames = [f"{accion}_{modelo}" for modelo, acciones in modelos.items()
                     for accion in acciones]
        grupo.permissions.set(
            Permission.objects.filter(content_type__app_label="apps", codename__in=codenames)
        )


class AppsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps"
    verbose_name = "Sonrisa Perfecta"

    def ready(self):
        post_migrate.connect(crear_roles, sender=self)
