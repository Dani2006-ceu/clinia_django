from datetime import date, time, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .forms import CitaForm, PacienteForm
from .models import Cita, Diagnostico, Especialidad, Odontologo, Paciente, Receta, Tratamiento


class BaseDatos(TestCase):
    def setUp(self):
        self.esp = Especialidad.objects.create(nombre="Ortodoncia")
        self.odo = Odontologo.objects.create(nombres="Ana", apellidos="Ríos", numero_colegiatura="COP-1",
                                             telefono="987654321", especialidad=self.esp)
        self.pac = Paciente.objects.create(nombres="Luis", apellidos="Pérez", dni="12345678",
                                           fecha_nacimiento=date(1990, 5, 1), telefono="912345678",
                                           direccion="Av. Lima 123")
        self.manana = date.today() + timedelta(days=1)
        self.cita = Cita.objects.create(paciente=self.pac, odontologo=self.odo, fecha=self.manana,
                                        hora=time(10, 0), motivo="Dolor de muela")
        self.diag = Diagnostico.objects.create(cita=self.cita, descripcion="Caries", fecha=self.manana)

    def usuario(self, rol):
        u = User.objects.create_user(f"u_{rol}", password="ClaveSegura123")
        u.groups.add(Group.objects.get(name=rol))
        self.client.login(username=u.username, password="ClaveSegura123")
        return u


class FormulariosTest(BaseDatos):
    def test_dni_invalido(self):
        f = PacienteForm(data={"nombres": "A", "apellidos": "B", "dni": "123", "fecha_nacimiento": "2000-01-01",
                               "telefono": "999999999", "direccion": "x"})
        self.assertIn("dni", f.errors)

    def test_cita_duplicada(self):
        f = CitaForm(data={"paciente": self.pac.pk, "odontologo": self.odo.pk, "fecha": self.manana,
                           "hora": "10:00", "motivo": "Control", "estado": "Pendiente"})
        self.assertFalse(f.is_valid())


class VistasTest(BaseDatos):
    def test_requiere_login(self):
        r = self.client.get(reverse("listado", args=["pacientes"]))
        self.assertEqual(r.status_code, 302)

    def test_registro_no_da_privilegios(self):
        self.client.post(reverse("registro"), {
            "username": "nuevo", "first_name": "N", "last_name": "U", "email": "n@x.com",
            "password1": "ClaveSegura123", "password2": "ClaveSegura123"})
        u = User.objects.get(username="nuevo")
        self.assertFalse(u.is_staff or u.is_superuser)
        self.assertTrue(u.groups.filter(name="Recepcionista").exists())

    def test_recepcion_no_ve_datos_clinicos(self):
        self.usuario("Recepcionista")
        self.assertEqual(self.client.get(reverse("listado", args=["pacientes"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("listado", args=["diagnosticos"])).status_code, 403)

    def test_crud_y_reportes_administrador(self):
        self.usuario("Administrador")
        for modulo in ["pacientes", "especialidades", "odontologos", "citas",
                       "diagnosticos", "tratamientos", "recetas"]:
            self.assertEqual(self.client.get(reverse("listado", args=[modulo]) + "?q=a").status_code, 200)
            self.assertEqual(self.client.get(reverse("crear", args=[modulo])).status_code, 200)
        for tipo in ["citas", "diagnosticos", "tratamientos", "recetas"]:
            self.assertEqual(self.client.get(reverse("reporte", args=[tipo])).status_code, 200)
            self.assertEqual(self.client.get(reverse("impresion", args=[tipo]) + "?estado=").status_code, 200)
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)

    def test_editar_y_eliminar_protegido(self):
        self.usuario("Administrador")
        r = self.client.post(reverse("crear", args=["tratamientos"]), {
            "diagnostico": self.diag.pk, "nombre": "Curación", "descripcion": "Resina",
            "fecha_inicio": self.manana, "costo": "150.00", "estado": "Pendiente"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Tratamiento.objects.count(), 1)
        # El paciente tiene citas: no debe poder borrarse
        self.client.post(reverse("eliminar", args=["pacientes", self.pac.pk]))
        self.assertTrue(Paciente.objects.filter(pk=self.pac.pk).exists())
        Receta.objects.create(diagnostico=self.diag, medicamento="Ibuprofeno", dosis="400 mg",
                              frecuencia="c/8h", duracion="3 días", fecha_emision=self.manana)
        rec = Receta.objects.get()
        self.client.post(reverse("eliminar", args=["recetas", rec.pk]))
        self.assertFalse(Receta.objects.exists())


class ModulosCompletosTest(TestCase):
    """Odontograma, caja, inventario, antecedentes, agenda, CRM y ficha 360."""

    def setUp(self):
        from django.core.management import call_command
        call_command("datos_demo", verbosity=0)
        self.pac = Paciente.objects.get(dni="45123678")

    def entrar(self, rol):
        u = User.objects.create_user(f"x_{rol}", password="ClaveSegura123")
        u.groups.add(Group.objects.get(name=rol))
        self.client.login(username=u.username, password="ClaveSegura123")

    def test_paginas_administrador(self):
        self.entrar("Administrador")
        receta = Receta.objects.first()
        for url in [reverse("inicio"), reverse("agenda"), reverse("agenda") + "?semana=2020-01-06",
                    reverse("crm"), reverse("ficha", args=[self.pac.pk]),
                    reverse("odontograma", args=[self.pac.pk]),
                    reverse("receta_imprimir", args=[receta.pk]),
                    reverse("reporte", args=["pagos"]), reverse("impresion", args=["pagos"])]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for modulo in ["antecedentes", "pagos", "insumos"]:
            self.assertEqual(self.client.get(reverse("listado", args=[modulo])).status_code, 200)
            self.assertEqual(self.client.get(reverse("crear", args=[modulo])).status_code, 200)

    def test_odontograma_guarda_pieza(self):
        self.entrar("Odontologo")
        r = self.client.post(reverse("odontograma", args=[self.pac.pk]),
                             {"pieza": 11, "estado": "Caries", "caras": "o, m", "observacion": ""})
        self.assertEqual(r.status_code, 302)
        pieza = self.pac.piezas.get(pieza=11)
        self.assertEqual((pieza.estado, pieza.caras), ("Caries", "MO"))

    def test_pago_no_supera_saldo(self):
        from .forms import PagoForm
        t = Tratamiento.objects.get(nombre="Endodoncia molar")  # costo 650, pagado 300
        f = PagoForm(data={"tratamiento": t.pk, "fecha": date.today(), "monto": "400.00",
                           "metodo": "Efectivo", "comprobante": "Boleta"})
        self.assertIn("monto", f.errors)
        f = PagoForm(data={"tratamiento": t.pk, "fecha": date.today(), "monto": "350.00",
                           "metodo": "Efectivo", "comprobante": "Boleta"})
        self.assertTrue(f.is_valid(), f.errors)

    def test_recepcion_no_ve_clinica_en_ficha(self):
        self.entrar("Recepcionista")
        r = self.client.get(reverse("ficha", args=[self.pac.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Penicilina")       # antecedente clínico oculto
        self.assertNotContains(r, "Caries profunda")  # diagnóstico oculto
        self.assertEqual(self.client.get(reverse("odontograma", args=[self.pac.pk])).status_code, 403)
