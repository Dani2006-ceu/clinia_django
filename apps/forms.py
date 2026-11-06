from datetime import date, time

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import (Antecedente, Cita, Diagnostico, Especialidad, Insumo, Odontologo, Paciente,
                     Pago, PiezaDental, Receta, Tratamiento)

FECHA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
HORA = forms.TimeInput(attrs={"type": "time"}, format="%H:%M")
TEXTO = forms.Textarea(attrs={"rows": 3})

HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(20, 0)


# ================================================================ Autenticación
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    recordar = forms.BooleanField(label="Mantener mi cuenta abierta", required=False)


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        correo = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return correo


# ================================================================ Filtros de reportes
class ReporteFiltroForm(forms.Form):
    desde = forms.DateField(label="Desde", required=False, widget=FECHA)
    hasta = forms.DateField(label="Hasta", required=False, widget=FECHA)
    paciente = forms.CharField(label="Paciente (nombre o DNI)", required=False, max_length=100)
    odontologo = forms.ModelChoiceField(
        label="Odontólogo", required=False, queryset=Odontologo.objects.all(),
        empty_label="Todos",
    )
    estado = forms.ChoiceField(label="Estado", required=False)

    def __init__(self, *args, estados=None, **kwargs):
        super().__init__(*args, **kwargs)
        if estados:
            self.fields["estado"].choices = [("", "Todos")] + list(estados)
        else:
            del self.fields["estado"]

    def clean(self):
        datos = super().clean()
        if datos.get("desde") and datos.get("hasta") and datos["desde"] > datos["hasta"]:
            raise forms.ValidationError("La fecha 'Desde' no puede ser mayor que 'Hasta'.")
        return datos


# ================================================================ Modelos de negocio
class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["nombres", "apellidos", "dni", "fecha_nacimiento",
                  "telefono", "direccion", "correo"]
        widgets = {
            "fecha_nacimiento": FECHA,
            "dni": forms.TextInput(attrs={"inputmode": "numeric", "maxlength": 8,
                                          "pattern": r"\d{8}"}),
        }

    def clean_fecha_nacimiento(self):
        f = self.cleaned_data["fecha_nacimiento"]
        if f > date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura.")
        if date.today().year - f.year > 120:
            raise forms.ValidationError("Verifique la fecha de nacimiento.")
        return f


class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ["nombre", "descripcion", "estado"]
        widgets = {"descripcion": TEXTO}


class OdontologoForm(forms.ModelForm):
    class Meta:
        model = Odontologo
        fields = ["nombres", "apellidos", "numero_colegiatura", "telefono",
                  "correo", "especialidad", "estado"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activas = Especialidad.objects.filter(estado=Especialidad.ACTIVA)
        if self.instance.pk:  # conservar la actual aunque se haya desactivado
            activas = activas | Especialidad.objects.filter(pk=self.instance.especialidad_id)
        self.fields["especialidad"].queryset = activas.distinct()


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ["paciente", "odontologo", "fecha", "hora", "motivo", "estado", "observaciones"]
        widgets = {"fecha": FECHA, "hora": HORA, "observaciones": TEXTO}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activos = Odontologo.objects.filter(estado=Odontologo.ACTIVO)
        if self.instance.pk:
            activos = activos | Odontologo.objects.filter(pk=self.instance.odontologo_id)
        self.fields["odontologo"].queryset = activos.distinct().select_related("especialidad")

    def clean_hora(self):
        h = self.cleaned_data["hora"]
        if not HORA_APERTURA <= h <= HORA_CIERRE:
            raise forms.ValidationError("El horario de atención es de 08:00 a 20:00.")
        return h

    def clean(self):
        datos = super().clean()
        fecha, hora = datos.get("fecha"), datos.get("hora")
        odontologo, estado = datos.get("odontologo"), datos.get("estado")
        if fecha and not self.instance.pk and fecha < date.today():
            self.add_error("fecha", "No se puede programar una cita en una fecha pasada.")
        if fecha and hora and odontologo and estado != Cita.CANCELADA:
            cruce = (Cita.objects.filter(odontologo=odontologo, fecha=fecha, hora=hora)
                     .exclude(estado=Cita.CANCELADA).exclude(pk=self.instance.pk))
            if cruce.exists():
                raise forms.ValidationError(
                    "El odontólogo ya tiene una cita registrada en esa fecha y hora."
                )
        return datos


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ["cita", "fecha", "descripcion", "recomendaciones"]
        widgets = {"fecha": FECHA, "descripcion": TEXTO, "recomendaciones": TEXTO}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cita"].queryset = (
            Cita.objects.exclude(estado=Cita.CANCELADA).select_related("paciente")
        )
        if not self.instance.pk:
            self.initial.setdefault("fecha", date.today())

    def clean(self):
        datos = super().clean()
        cita, fecha = datos.get("cita"), datos.get("fecha")
        if cita and fecha and fecha < cita.fecha:
            self.add_error("fecha", "El diagnóstico no puede ser anterior a la cita.")
        return datos


class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = ["diagnostico", "nombre", "descripcion", "fecha_inicio",
                  "fecha_fin", "costo", "estado"]
        widgets = {"fecha_inicio": FECHA, "fecha_fin": FECHA, "descripcion": TEXTO,
                   "costo": forms.NumberInput(attrs={"min": "0", "step": "0.01"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["diagnostico"].queryset = Diagnostico.objects.select_related("cita__paciente")

    def clean(self):
        datos = super().clean()
        inicio, fin, estado = datos.get("fecha_inicio"), datos.get("fecha_fin"), datos.get("estado")
        if inicio and fin and fin < inicio:
            self.add_error("fecha_fin", "La fecha de fin no puede ser anterior a la de inicio.")
        if estado == Tratamiento.FINALIZADO and not fin:
            self.add_error("fecha_fin", "Indique la fecha de finalización.")
        return datos


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ["diagnostico", "medicamento", "dosis", "frecuencia",
                  "duracion", "indicaciones", "fecha_emision"]
        widgets = {"fecha_emision": FECHA, "indicaciones": TEXTO}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["diagnostico"].queryset = Diagnostico.objects.select_related("cita__paciente")
        if not self.instance.pk:
            self.initial.setdefault("fecha_emision", date.today())

    def clean(self):
        datos = super().clean()
        diag, fecha = datos.get("diagnostico"), datos.get("fecha_emision")
        if diag and fecha and fecha < diag.fecha:
            self.add_error("fecha_emision", "La receta no puede ser anterior al diagnóstico.")
        return datos


# ================================================================ Módulos complementarios
class AntecedenteForm(forms.ModelForm):
    class Meta:
        model = Antecedente
        fields = ["paciente", "alergias", "enfermedades", "medicamentos", "cirugias",
                  "embarazo", "fuma", "observaciones"]
        widgets = {c: forms.Textarea(attrs={"rows": 2}) for c in
                   ["alergias", "enfermedades", "medicamentos", "cirugias", "observaciones"]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        libres = Paciente.objects.filter(antecedente__isnull=True)
        if self.instance.pk:
            libres = libres | Paciente.objects.filter(pk=self.instance.paciente_id)
        self.fields["paciente"].queryset = libres.distinct()


class PiezaDentalForm(forms.ModelForm):
    class Meta:
        model = PiezaDental
        fields = ["pieza", "estado", "caras", "observacion"]

    def clean_caras(self):
        caras = self.cleaned_data["caras"].upper().replace(" ", "").replace(",", "")
        if any(c not in "VLMDO" for c in caras):
            raise forms.ValidationError("Use solo las letras V, L, M, D u O.")
        return "".join(sorted(set(caras), key="VLMDO".index))


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["tratamiento", "fecha", "monto", "metodo", "comprobante",
                  "numero_comprobante", "observacion"]
        widgets = {"fecha": FECHA,
                   "monto": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tratamiento"].queryset = Tratamiento.objects.select_related(
            "diagnostico__cita__paciente")
        if not self.instance.pk:
            self.initial.setdefault("fecha", date.today())

    def clean_fecha(self):
        f = self.cleaned_data["fecha"]
        if f > date.today():
            raise forms.ValidationError("No se puede registrar un pago con fecha futura.")
        return f

    def clean(self):
        datos = super().clean()
        trat, monto = datos.get("tratamiento"), datos.get("monto")
        if trat and monto:
            anterior = self.instance.monto if self.instance.pk and self.instance.tratamiento_id == trat.pk else 0
            disponible = trat.saldo + anterior
            if monto > disponible:
                self.add_error("monto", f"El monto supera el saldo pendiente (S/ {disponible:,.2f}).")
        return datos


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ["codigo", "nombre", "categoria", "unidad", "stock", "stock_minimo",
                  "precio", "fecha_vencimiento"]
        widgets = {"fecha_vencimiento": FECHA,
                   "precio": forms.NumberInput(attrs={"min": "0", "step": "0.01"})}

    def clean_codigo(self):
        return self.cleaned_data["codigo"].strip().upper()
