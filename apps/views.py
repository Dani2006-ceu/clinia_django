"""
Vistas del sistema Sonrisa Perfecta.

El CRUD de los siete modelos usa vistas genéricas configuradas con el
diccionario MODULOS: cada entrada indica el modelo, su formulario, las
columnas del listado y los campos de búsqueda.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, F, Max, ProtectedError, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .apps import ROL_POR_DEFECTO
from .forms import (AntecedenteForm, CitaForm, DiagnosticoForm, EspecialidadForm, InsumoForm,
                    LoginForm, OdontologoForm, PacienteForm, PagoForm, PiezaDentalForm, RecetaForm,
                    RegistroForm, ReporteFiltroForm, TratamientoForm)
from .models import (Antecedente, Cita, Diagnostico, Especialidad, Insumo, Odontologo, Paciente,
                     Pago, PiezaDental, Receta, Tratamiento)
from .models.PiezaDental import INFERIOR, SUPERIOR

# ====================================================================== Configuración
MODULOS = {
    "pacientes": {
        "modelo": Paciente, "form": PacienteForm,
        "titulo": "Pacientes", "singular": "paciente",
        "columnas": [("dni", "DNI"), ("apellidos", "Apellidos"), ("nombres", "Nombres"),
                     ("edad", "Edad"), ("telefono", "Teléfono"), ("correo", "Correo")],
        "buscar": ["nombres", "apellidos", "dni", "telefono"],
        "acciones": [("ficha", "Ficha 360°"), ("odontograma", "Odontograma")],
    },
    "especialidades": {
        "modelo": Especialidad, "form": EspecialidadForm,
        "titulo": "Especialidades", "singular": "especialidad",
        "columnas": [("nombre", "Nombre"), ("descripcion", "Descripción"), ("estado", "Estado")],
        "buscar": ["nombre", "descripcion"],
    },
    "odontologos": {
        "modelo": Odontologo, "form": OdontologoForm,
        "titulo": "Odontólogos", "singular": "odontólogo",
        "columnas": [("numero_colegiatura", "COP"), ("apellidos", "Apellidos"),
                     ("nombres", "Nombres"), ("especialidad", "Especialidad"),
                     ("telefono", "Teléfono"), ("estado", "Estado")],
        "buscar": ["nombres", "apellidos", "numero_colegiatura", "especialidad__nombre"],
        "relacionados": ["especialidad"],
    },
    "citas": {
        "modelo": Cita, "form": CitaForm,
        "titulo": "Citas", "singular": "cita",
        "columnas": [("fecha", "Fecha"), ("hora", "Hora"), ("paciente.nombre_completo", "Paciente"),
                     ("odontologo", "Odontólogo"), ("motivo", "Motivo"), ("estado", "Estado")],
        "buscar": ["paciente__nombres", "paciente__apellidos", "paciente__dni",
                   "odontologo__apellidos", "motivo", "estado"],
        "relacionados": ["paciente", "odontologo"],
    },
    "diagnosticos": {
        "modelo": Diagnostico, "form": DiagnosticoForm,
        "titulo": "Diagnósticos", "singular": "diagnóstico",
        "columnas": [("id", "N.º"), ("fecha", "Fecha"), ("cita.paciente.nombre_completo", "Paciente"),
                     ("cita.odontologo", "Odontólogo"), ("descripcion", "Diagnóstico")],
        "buscar": ["descripcion", "cita__paciente__nombres", "cita__paciente__apellidos",
                   "cita__paciente__dni"],
        "relacionados": ["cita__paciente", "cita__odontologo"],
    },
    "tratamientos": {
        "modelo": Tratamiento, "form": TratamientoForm,
        "titulo": "Tratamientos", "singular": "tratamiento",
        "columnas": [("nombre", "Tratamiento"), ("diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("fecha_inicio", "Inicio"), ("fecha_fin", "Fin"), ("costo", "Costo"),
                     ("estado", "Estado")],
        "buscar": ["nombre", "diagnostico__cita__paciente__nombres",
                   "diagnostico__cita__paciente__apellidos", "diagnostico__cita__paciente__dni"],
        "relacionados": ["diagnostico__cita__paciente"],
    },
    "recetas": {
        "modelo": Receta, "form": RecetaForm,
        "titulo": "Recetas", "singular": "receta",
        "columnas": [("fecha_emision", "Emisión"), ("diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("medicamento", "Medicamento"), ("dosis", "Dosis"),
                     ("frecuencia", "Frecuencia"), ("duracion", "Duración")],
        "buscar": ["medicamento", "diagnostico__cita__paciente__nombres",
                   "diagnostico__cita__paciente__apellidos", "diagnostico__cita__paciente__dni"],
        "relacionados": ["diagnostico__cita__paciente"],
        "acciones": [("receta_imprimir", "Imprimir")],
    },
    "antecedentes": {
        "modelo": Antecedente, "form": AntecedenteForm,
        "titulo": "Antecedentes médicos", "singular": "antecedente médico",
        "columnas": [("paciente.nombre_completo", "Paciente"), ("alergias", "Alergias"),
                     ("enfermedades", "Enfermedades"), ("embarazo", "Embarazo"), ("fuma", "Fuma")],
        "buscar": ["paciente__nombres", "paciente__apellidos", "paciente__dni", "alergias",
                   "enfermedades"],
        "relacionados": ["paciente"],
    },
    "pagos": {
        "modelo": Pago, "form": PagoForm,
        "titulo": "Caja y pagos", "singular": "pago",
        "columnas": [("fecha", "Fecha"), ("tratamiento.diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("tratamiento.nombre", "Tratamiento"), ("monto", "Monto"), ("metodo", "Método"),
                     ("comprobante", "Comprobante"), ("numero_comprobante", "N.º")],
        "buscar": ["tratamiento__nombre", "tratamiento__diagnostico__cita__paciente__nombres",
                   "tratamiento__diagnostico__cita__paciente__apellidos",
                   "tratamiento__diagnostico__cita__paciente__dni", "numero_comprobante"],
        "relacionados": ["tratamiento__diagnostico__cita__paciente"],
    },
    "insumos": {
        "modelo": Insumo, "form": InsumoForm,
        "titulo": "Inventario", "singular": "insumo",
        "columnas": [("codigo", "Código"), ("nombre", "Insumo"), ("categoria", "Categoría"),
                     ("stock", "Stock"), ("stock_minimo", "Mínimo"), ("precio", "Precio"),
                     ("fecha_vencimiento", "Vence"), ("estado", "Estado")],
        "buscar": ["codigo", "nombre", "categoria"],
    },
}

REPORTES = {
    "citas": {
        "modelo": Cita, "titulo": "Reporte de citas",
        "fecha": "fecha", "paciente": "paciente", "odontologo": "odontologo",
        "estados": Cita.ESTADOS,
        "relacionados": ["paciente", "odontologo__especialidad"],
        "columnas": [("fecha", "Fecha"), ("hora", "Hora"), ("paciente.nombre_completo", "Paciente"),
                     ("paciente.dni", "DNI"), ("odontologo", "Odontólogo"),
                     ("motivo", "Motivo"), ("estado", "Estado")],
    },
    "diagnosticos": {
        "modelo": Diagnostico, "titulo": "Reporte de diagnósticos",
        "fecha": "fecha", "paciente": "cita__paciente", "odontologo": "cita__odontologo",
        "relacionados": ["cita__paciente", "cita__odontologo"],
        "columnas": [("fecha", "Fecha"), ("cita.paciente.nombre_completo", "Paciente"),
                     ("cita.paciente.dni", "DNI"), ("cita.odontologo", "Odontólogo"),
                     ("descripcion", "Diagnóstico"), ("recomendaciones", "Recomendaciones")],
    },
    "tratamientos": {
        "modelo": Tratamiento, "titulo": "Reporte de tratamientos",
        "fecha": "fecha_inicio", "paciente": "diagnostico__cita__paciente",
        "odontologo": "diagnostico__cita__odontologo", "estados": Tratamiento.ESTADOS,
        "total": "costo",
        "relacionados": ["diagnostico__cita__paciente", "diagnostico__cita__odontologo"],
        "columnas": [("fecha_inicio", "Inicio"), ("fecha_fin", "Fin"),
                     ("diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("nombre", "Tratamiento"), ("diagnostico.cita.odontologo", "Odontólogo"),
                     ("estado", "Estado"), ("costo", "Costo")],
    },
    "recetas": {
        "modelo": Receta, "titulo": "Reporte de recetas",
        "fecha": "fecha_emision", "paciente": "diagnostico__cita__paciente",
        "odontologo": "diagnostico__cita__odontologo",
        "relacionados": ["diagnostico__cita__paciente", "diagnostico__cita__odontologo"],
        "columnas": [("fecha_emision", "Emisión"), ("diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("medicamento", "Medicamento"), ("dosis", "Dosis"),
                     ("frecuencia", "Frecuencia"), ("duracion", "Duración"),
                     ("indicaciones", "Indicaciones"), ("diagnostico.cita.odontologo", "Prescrito por")],
    },
    "pagos": {
        "modelo": Pago, "titulo": "Reporte de pagos",
        "fecha": "fecha", "paciente": "tratamiento__diagnostico__cita__paciente",
        "odontologo": "tratamiento__diagnostico__cita__odontologo", "total": "monto",
        "relacionados": ["tratamiento__diagnostico__cita__paciente"],
        "columnas": [("fecha", "Fecha"), ("tratamiento.diagnostico.cita.paciente.nombre_completo", "Paciente"),
                     ("tratamiento.diagnostico.cita.paciente.dni", "DNI"), ("tratamiento.nombre", "Tratamiento"),
                     ("metodo", "Método"), ("comprobante", "Comprobante"),
                     ("numero_comprobante", "N.º"), ("monto", "Monto")],
    },
}


# ====================================================================== Utilidades
def permiso(modelo, accion):
    return f"apps.{accion}_{modelo._meta.model_name}"


def exigir(request, modelo, accion):
    """Lanza 403 si el usuario no tiene el permiso de su puesto."""
    if not request.user.has_perm(permiso(modelo, accion)):
        raise PermissionDenied


def obtener_config(diccionario, clave):
    try:
        return diccionario[clave]
    except KeyError:
        raise Http404


def valor(obj, ruta):
    """Lee 'a.b.c' de un objeto y lo convierte en texto legible."""
    for parte in ruta.split("."):
        if obj is None:
            break
        display = getattr(obj, f"get_{parte}_display", None)
        obj = display() if display else getattr(obj, parte)
    if obj is None or obj == "":
        return "—"
    if isinstance(obj, bool):
        return "Sí" if obj else "No"
    if isinstance(obj, datetime):
        return timezone.localtime(obj).strftime("%d/%m/%Y %H:%M")
    if isinstance(obj, date):
        return obj.strftime("%d/%m/%Y")
    if isinstance(obj, time):
        return obj.strftime("%H:%M")
    if isinstance(obj, Decimal):
        return f"S/ {obj:,.2f}"
    return str(obj)


def construir_filas(objetos, columnas):
    filas = []
    for obj in objetos:
        celdas = []
        for ruta, _ in columnas:
            texto = valor(obj, ruta)
            clase = f"badge badge-{slugify(texto)}" if ruta == "estado" else ""
            celdas.append({"texto": texto, "clase": clase})
        filas.append({"pk": obj.pk, "celdas": celdas})
    return filas


def menu_context(request):
    """Procesador de contexto: menú lateral según los permisos del usuario."""
    if not request.user.is_authenticated:
        return {}
    menu = [{"slug": s, "titulo": c["titulo"]} for s, c in MODULOS.items()
            if request.user.has_perm(permiso(c["modelo"], "view"))]
    reportes = [{"slug": s, "titulo": c["titulo"].replace("Reporte de ", "").capitalize()}
                for s, c in REPORTES.items()
                if request.user.has_perm(permiso(c["modelo"], "view"))]
    return {"menu_modulos": menu, "menu_reportes": reportes}


# ====================================================================== Autenticación
class LoginVista(auth_views.LoginView):
    template_name = "control/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        if form.cleaned_data.get("recordar"):
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            self.request.session.set_expiry(0)  # expira al cerrar el navegador
        return respuesta


def registro(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save(commit=False)
        usuario.is_staff = False       # nunca se otorgan privilegios
        usuario.is_superuser = False   # administrativos al registrarse
        usuario.save()
        grupo, _ = Group.objects.get_or_create(name=ROL_POR_DEFECTO)
        usuario.groups.add(grupo)
        messages.success(request, "Cuenta creada. Ya puede iniciar sesión.")
        return redirect("login")
    return render(request, "control/registro.html", {"form": form})


# ====================================================================== Dashboard
@never_cache
@login_required
def inicio(request):
    hoy = timezone.localdate()
    u = request.user
    ctx = {"hoy": hoy, "indicadores": []}

    def agregar(modelo, titulo, valor_, detalle, slug):
        if u.has_perm(permiso(modelo, "view")):
            ctx["indicadores"].append(
                {"titulo": titulo, "valor": valor_, "detalle": detalle, "slug": slug})

    agregar(Paciente, "Pacientes", Paciente.objects.count(),
            f"{Paciente.objects.filter(created_at__date__gte=hoy.replace(day=1)).count()} nuevos este mes",
            "pacientes")
    agregar(Cita, "Citas de hoy", Cita.objects.filter(fecha=hoy).exclude(estado=Cita.CANCELADA).count(),
            f"{Cita.objects.filter(fecha__gte=hoy, estado__in=[Cita.PENDIENTE, Cita.CONFIRMADA]).count()} por atender",
            "citas")
    agregar(Diagnostico, "Diagnósticos", Diagnostico.objects.count(),
            f"{Diagnostico.objects.filter(fecha__year=hoy.year, fecha__month=hoy.month).count()} este mes",
            "diagnosticos")
    agregar(Tratamiento, "Tratamientos", Tratamiento.objects.count(),
            f"{Tratamiento.objects.filter(estado=Tratamiento.EN_PROCESO).count()} en proceso",
            "tratamientos")

    if u.has_perm("apps.view_cita"):
        conteo = dict(Cita.objects.values_list("estado").annotate(n=Count("id")))
        total = sum(conteo.values()) or 1
        ctx["citas_estado"] = [
            {"estado": e, "n": conteo.get(e, 0), "pct": round(conteo.get(e, 0) * 100 / total),
             "clase": slugify(e)} for e, _ in Cita.ESTADOS
        ]
        ctx["proximas"] = (Cita.objects.filter(fecha__gte=hoy)
                           .exclude(estado__in=[Cita.CANCELADA, Cita.ATENDIDA])
                           .select_related("paciente", "odontologo")
                           .order_by("fecha", "hora")[:8])
    if u.has_perm("apps.view_tratamiento"):
        ctx["ingresos_mes"] = (Tratamiento.objects
                               .filter(fecha_inicio__year=hoy.year, fecha_inicio__month=hoy.month)
                               .exclude(estado=Tratamiento.PENDIENTE)
                               .aggregate(s=Sum("costo"))["s"] or Decimal("0"))
    if u.has_perm("apps.view_pago"):
        ctx["cobrado_mes"] = (Pago.objects.filter(fecha__year=hoy.year, fecha__month=hoy.month)
                              .aggregate(s=Sum("monto"))["s"] or Decimal("0"))
        ctx["por_cobrar"] = sum((t.saldo_calc for t in tratamientos_con_saldo()), Decimal("0"))
    if u.has_perm("apps.view_insumo"):
        ctx["stock_bajo"] = Insumo.objects.filter(stock__lte=F("stock_minimo")).order_by("stock")[:6]
    if u.has_perm("apps.view_cita"):
        ctx["por_confirmar"] = Cita.objects.filter(
            estado=Cita.PENDIENTE, fecha__range=(hoy, hoy + timedelta(days=1))).count()
    return render(request, "control/inicio.html", ctx)


# ====================================================================== CRUD genérico
@never_cache
@login_required
def listado(request, modulo):
    cfg = obtener_config(MODULOS, modulo)
    modelo = cfg["modelo"]
    exigir(request, modelo, "view")

    qs = modelo.objects.select_related(*cfg.get("relacionados", []))
    q = request.GET.get("q", "").strip()
    if q:
        filtro = Q()
        for campo in cfg["buscar"]:
            filtro |= Q(**{f"{campo}__icontains": q})
        qs = qs.filter(filtro)

    pagina = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "control/listado.html", {
        "cfg": cfg, "modulo": modulo, "q": q, "pagina": pagina,
        "encabezados": [c[1] for c in cfg["columnas"]],
        "filas": construir_filas(pagina.object_list, cfg["columnas"]),
        "puede_crear": request.user.has_perm(permiso(modelo, "add")),
        "puede_editar": request.user.has_perm(permiso(modelo, "change")),
        "puede_eliminar": request.user.has_perm(permiso(modelo, "delete")),
    })


@never_cache
@login_required
def formulario(request, modulo, pk=None):
    cfg = obtener_config(MODULOS, modulo)
    modelo = cfg["modelo"]
    instancia = get_object_or_404(modelo, pk=pk) if pk else None
    exigir(request, modelo, "change" if instancia else "add")

    form = cfg["form"](request.POST or None, instance=instancia)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            accion = "actualizado" if instancia else "registrado"
            messages.success(request, f"Registro de {cfg['singular']} {accion} correctamente.")
            return redirect("listado", modulo=modulo)
        messages.error(request, "Revise los campos marcados en rojo.")
    return render(request, "control/formulario.html", {
        "cfg": cfg, "modulo": modulo, "form": form, "instancia": instancia,
    })


@login_required
@require_POST
def eliminar(request, modulo, pk):
    cfg = obtener_config(MODULOS, modulo)
    modelo = cfg["modelo"]
    exigir(request, modelo, "delete")
    obj = get_object_or_404(modelo, pk=pk)
    try:
        obj.delete()
        messages.success(request, f"Registro de {cfg['singular']} eliminado.")
    except ProtectedError:
        messages.error(request, f"No se puede eliminar: el {cfg['singular']} tiene "
                                "registros relacionados. Elimínelos primero.")
    return redirect(f"{reverse('listado', args=[modulo])}?{request.GET.urlencode()}")


# ====================================================================== Reportes
def datos_reporte(request, tipo):
    cfg = obtener_config(REPORTES, tipo)
    exigir(request, cfg["modelo"], "view")
    form = ReporteFiltroForm(request.GET or None, estados=cfg.get("estados"))
    qs = cfg["modelo"].objects.select_related(*cfg["relacionados"])
    if form.is_valid():
        d = form.cleaned_data
        if d.get("desde"):
            qs = qs.filter(**{f"{cfg['fecha']}__gte": d["desde"]})
        if d.get("hasta"):
            qs = qs.filter(**{f"{cfg['fecha']}__lte": d["hasta"]})
        if d.get("odontologo"):
            qs = qs.filter(**{cfg["odontologo"]: d["odontologo"]})
        if d.get("estado"):
            qs = qs.filter(estado=d["estado"])
        if d.get("paciente"):
            p = cfg["paciente"]
            texto = d["paciente"]
            qs = qs.filter(Q(**{f"{p}__nombres__icontains": texto})
                           | Q(**{f"{p}__apellidos__icontains": texto})
                           | Q(**{f"{p}__dni__icontains": texto}))
    elif form.is_bound:
        qs = qs.none()
    qs = qs.order_by(cfg["fecha"])
    total = None
    if cfg.get("total"):
        total = qs.aggregate(s=Sum(cfg["total"]))["s"] or Decimal("0")
    return {
        "cfg": cfg, "tipo": tipo, "form": form,
        "encabezados": [c[1] for c in cfg["columnas"]],
        "filas": construir_filas(qs, cfg["columnas"]),
        "cantidad": qs.count(), "total": f"S/ {total:,.2f}" if total is not None else None,
        "query": request.GET.urlencode(),
    }


@never_cache
@login_required
def reporte(request, tipo):
    ctx = datos_reporte(request, tipo)
    return render(request, "control/reporte.html", ctx)


@never_cache
@login_required
def impresion(request, tipo):
    ctx = datos_reporte(request, tipo)
    ctx["generado"] = timezone.localtime()
    ctx["filtros"] = [(f.label, f.value()) for f in ctx["form"]
                      if f.value() not in (None, "")]
    for i, (etiqueta, v) in enumerate(ctx["filtros"]):
        if etiqueta == "Odontólogo" and str(v).isdigit():
            ctx["filtros"][i] = (etiqueta, Odontologo.objects.filter(pk=v).first())
    return render(request, "control/impresion.html", ctx)


# ====================================================================== Caja: saldos
def tratamientos_con_saldo(qs=None):
    """Tratamientos aceptados (en proceso o finalizados) que aún tienen saldo por cobrar."""
    qs = qs if qs is not None else Tratamiento.objects.all()
    cero = Value(Decimal("0.00"), output_field=DecimalField(max_digits=10, decimal_places=2))
    return (qs.exclude(estado=Tratamiento.PENDIENTE)
            .annotate(pagado_calc=Coalesce(Sum("pagos__monto"), cero))
            .annotate(saldo_calc=F("costo") - F("pagado_calc"))
            .filter(saldo_calc__gt=0)
            .select_related("diagnostico__cita__paciente"))


# ====================================================================== Ficha 360° del paciente
@never_cache
@login_required
def ficha(request, pk):
    exigir(request, Paciente, "view")
    paciente = get_object_or_404(Paciente, pk=pk)
    u = request.user
    ctx = {"p": paciente, "hoy": timezone.localdate()}
    ctx["ver_antecedentes"] = u.has_perm("apps.view_antecedente")
    ctx["antecedente"] = (Antecedente.objects.filter(paciente=paciente).first()
                          if ctx["ver_antecedentes"] else None)
    if u.has_perm("apps.view_cita"):
        ctx["citas"] = paciente.citas.select_related("odontologo").order_by("-fecha", "-hora")
        ctx["proxima"] = (paciente.citas.filter(fecha__gte=ctx["hoy"])
                          .exclude(estado__in=[Cita.CANCELADA, Cita.ATENDIDA])
                          .order_by("fecha", "hora").first())
    if u.has_perm("apps.view_diagnostico"):
        ctx["diagnosticos"] = (Diagnostico.objects.filter(cita__paciente=paciente)
                               .select_related("cita__odontologo").order_by("-fecha"))
    if u.has_perm("apps.view_tratamiento"):
        cero = Value(Decimal("0.00"), output_field=DecimalField(max_digits=10, decimal_places=2))
        trats = list(Tratamiento.objects.filter(diagnostico__cita__paciente=paciente)
                     .annotate(pagado_calc=Coalesce(Sum("pagos__monto"), cero))
                     .order_by("-fecha_inicio"))
        ctx["tratamientos"] = trats
        aceptados = [t for t in trats if t.estado != Tratamiento.PENDIENTE]
        ctx["total_tratamientos"] = sum((t.costo for t in aceptados), Decimal("0"))
        ctx["total_pagado"] = sum((t.pagado_calc for t in trats), Decimal("0"))
        ctx["saldo"] = max(ctx["total_tratamientos"] - ctx["total_pagado"], Decimal("0"))
    if u.has_perm("apps.view_receta"):
        ctx["recetas"] = (Receta.objects.filter(diagnostico__cita__paciente=paciente)
                          .order_by("-fecha_emision"))
    if u.has_perm("apps.view_pago"):
        ctx["pagos"] = (Pago.objects.filter(tratamiento__diagnostico__cita__paciente=paciente)
                        .select_related("tratamiento"))
    if u.has_perm("apps.view_piezadental"):
        ctx["ver_odontograma"] = True
        ctx["odonto_resumen"] = (paciente.piezas.exclude(estado=PiezaDental.SANO)
                                 .values("estado").annotate(n=Count("id")).order_by("-n"))
    return render(request, "control/ficha.html", ctx)


# ====================================================================== Odontograma
@never_cache
@login_required
def odontograma(request, pk):
    exigir(request, PiezaDental, "view")
    paciente = get_object_or_404(Paciente, pk=pk)
    puede_editar = request.user.has_perm("apps.change_piezadental")
    form = PiezaDentalForm()
    if request.method == "POST":
        if not puede_editar:
            raise PermissionDenied
        existente = PiezaDental.objects.filter(
            paciente=paciente, pieza=request.POST.get("pieza") or 0).first()
        form = PiezaDentalForm(request.POST, instance=existente)
        if form.is_valid():
            pieza = form.save(commit=False)
            pieza.paciente = paciente
            pieza.save()
            messages.success(request, f"Pieza {pieza.pieza} actualizada: {pieza.estado}.")
            return redirect("odontograma", pk=pk)
        messages.error(request, "Revise los datos de la pieza.")
    registros = {p.pieza: p for p in paciente.piezas.all()}

    def fila(numeros):
        salida = []
        for n in numeros:
            reg = registros.get(n)
            estado = reg.estado if reg else PiezaDental.SANO
            salida.append({"n": n, "reg": reg, "estado": estado, "clase": slugify(estado)})
        return salida

    return render(request, "control/odontograma.html", {
        "p": paciente, "form": form, "puede_editar": puede_editar,
        "superior": fila(SUPERIOR), "inferior": fila(INFERIOR),
        "estados": [(e, slugify(e)) for e, _ in PiezaDental.ESTADOS],
        "registros": [r for r in registros.values() if r.estado != PiezaDental.SANO],
    })


# ====================================================================== Agenda semanal
@never_cache
@login_required
def agenda(request):
    exigir(request, Cita, "view")
    hoy = timezone.localdate()
    try:
        ref = date.fromisoformat(request.GET.get("semana", ""))
    except ValueError:
        ref = hoy
    lunes = ref - timedelta(days=ref.weekday())
    dias = [lunes + timedelta(days=i) for i in range(6)]  # lunes a sábado
    odontologo_id = request.GET.get("odontologo", "")
    citas = (Cita.objects.filter(fecha__range=(dias[0], dias[-1]))
             .select_related("paciente", "odontologo").order_by("hora"))
    if odontologo_id.isdigit():
        citas = citas.filter(odontologo_id=odontologo_id)
    celdas = {}
    for c in citas:
        celdas.setdefault((c.fecha, c.hora.hour), []).append(c)
    filas = [{"hora": f"{h:02d}:00", "celdas": [{"dia": d, "citas": celdas.get((d, h), [])} for d in dias]}
             for h in range(8, 21)]
    return render(request, "control/agenda.html", {
        "dias": dias, "filas": filas, "hoy": hoy, "total": len(citas),
        "anterior": (lunes - timedelta(days=7)).isoformat(),
        "siguiente": (lunes + timedelta(days=7)).isoformat(),
        "actual": hoy.isoformat(),
        "odontologos": Odontologo.objects.filter(estado=Odontologo.ACTIVO),
        "odontologo_id": odontologo_id,
        "puede_editar": request.user.has_perm("apps.change_cita"),
        "puede_crear": request.user.has_perm("apps.add_cita"),
    })


# ====================================================================== CRM
@never_cache
@login_required
def crm(request):
    exigir(request, Paciente, "view")
    u = request.user
    hoy = timezone.localdate()
    ctx = {"hoy": hoy}
    if u.has_perm("apps.view_cita"):
        ctx["por_confirmar"] = (Cita.objects.filter(estado=Cita.PENDIENTE,
                                                    fecha__range=(hoy, hoy + timedelta(days=2)))
                                .select_related("paciente", "odontologo").order_by("fecha", "hora"))
        ctx["por_confirmar"] = list(ctx["por_confirmar"])
        for c in ctx["por_confirmar"]:
            c.mensaje = (f"Hola {c.paciente.nombres}, le recordamos su cita en Sonrisa Perfecta el "
                         f"{c.fecha:%d/%m/%Y} a las {c.hora:%H:%M} con {c.odontologo}. "
                         "¿Nos confirma su asistencia?")
        ctx["inactivos"] = (Paciente.objects
                            .annotate(ultima=Max("citas__fecha", filter=Q(citas__estado=Cita.ATENDIDA)),
                                      futuras=Count("citas", filter=Q(citas__fecha__gte=hoy)
                                                    & ~Q(citas__estado=Cita.CANCELADA)))
                            .filter(ultima__lt=hoy - timedelta(days=180), futuras=0)
                            .order_by("ultima")[:30])
        conteo = dict(Cita.objects.filter(fecha__range=(hoy - timedelta(days=90), hoy))
                      .values_list("estado").annotate(n=Count("id")))
        total = sum(conteo.values())
        ctx["embudo"] = [{"estado": e, "n": conteo.get(e, 0),
                          "pct": round(conteo.get(e, 0) * 100 / total) if total else 0,
                          "clase": slugify(e)} for e, _ in Cita.ESTADOS]
        cerradas = conteo.get(Cita.ATENDIDA, 0) + conteo.get(Cita.CANCELADA, 0)
        ctx["asistencia"] = round(conteo.get(Cita.ATENDIDA, 0) * 100 / cerradas) if cerradas else None
        ctx["total_90"] = total
    if u.has_perm("apps.view_tratamiento"):
        ctx["atrasados"] = (Tratamiento.objects
                            .filter(Q(estado=Tratamiento.EN_PROCESO, fecha_fin__lt=hoy)
                                    | Q(estado=Tratamiento.PENDIENTE,
                                        fecha_inicio__lt=hoy - timedelta(days=15)))
                            .select_related("diagnostico__cita__paciente")
                            .order_by("fecha_inicio")[:30])
    if u.has_perm("apps.view_pago"):
        deudores = list(tratamientos_con_saldo().order_by("-saldo_calc"))
        ctx["deudores"] = deudores[:30]
        ctx["deuda_total"] = sum((t.saldo_calc for t in deudores), Decimal("0"))
    ctx["cumpleanos"] = (Paciente.objects.filter(fecha_nacimiento__month=hoy.month)
                         .order_by("fecha_nacimiento__day"))
    return render(request, "control/crm.html", ctx)


# ====================================================================== Receta imprimible
@never_cache
@login_required
def receta_imprimir(request, pk):
    exigir(request, Receta, "view")
    receta = get_object_or_404(
        Receta.objects.select_related("diagnostico__cita__paciente",
                                      "diagnostico__cita__odontologo__especialidad"), pk=pk)
    paciente = receta.diagnostico.cita.paciente
    return render(request, "control/receta.html", {
        "r": receta, "p": paciente, "o": receta.diagnostico.cita.odontologo,
        "otras": Receta.objects.filter(diagnostico=receta.diagnostico).exclude(pk=pk).order_by("id"),
        "antecedente": Antecedente.objects.filter(paciente=paciente).first(),
        "generado": timezone.localtime(),
    })
