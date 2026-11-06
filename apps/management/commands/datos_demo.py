"""Carga datos de demostración: python manage.py datos_demo"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.models import (Antecedente, Cita, Diagnostico, Especialidad, Insumo, Odontologo,
                         Paciente, Pago, PiezaDental, Receta, Tratamiento)


class Command(BaseCommand):
    help = "Crea datos de ejemplo para demostrar el sistema (solo si no hay pacientes)."

    @transaction.atomic
    def handle(self, *args, **options):
        if Paciente.objects.exists():
            self.stdout.write(self.style.WARNING("Ya existen pacientes; no se cargaron datos demo."))
            return
        hoy = date.today()

        esp = {n: Especialidad.objects.create(nombre=n, descripcion=d) for n, d in [
            ("Odontología general", "Consultas, limpiezas y restauraciones."),
            ("Ortodoncia", "Corrección de la posición dental con brackets y alineadores."),
            ("Endodoncia", "Tratamiento de conductos."),
            ("Periodoncia", "Tratamiento de encías."),
        ]}
        odo = [
            Odontologo.objects.create(nombres="María", apellidos="Torres Vega", numero_colegiatura="COP-24518",
                                      telefono="987111222", correo="mtorres@sonrisa.pe",
                                      especialidad=esp["Odontología general"]),
            Odontologo.objects.create(nombres="Carlos", apellidos="Ramírez Soto", numero_colegiatura="COP-19873",
                                      telefono="987333444", correo="cramirez@sonrisa.pe",
                                      especialidad=esp["Ortodoncia"]),
            Odontologo.objects.create(nombres="Lucía", apellidos="Paredes Lazo", numero_colegiatura="COP-30112",
                                      telefono="987555666", correo="lparedes@sonrisa.pe",
                                      especialidad=esp["Endodoncia"]),
        ]
        datos = [
            ("Ana", "García López", "45123678", date(1990, hoy.month, min(hoy.day + 3, 28)), "912345678"),
            ("Jorge", "Mendoza Ríos", "41234567", date(1985, 3, 12), "923456789"),
            ("Rosa", "Quispe Huamán", "47896541", date(1998, 7, 25), "934567890"),
            ("Luis", "Fernández Cruz", "40112233", date(1978, 11, 2), "945678901"),
            ("Carmen", "Salazar Díaz", "46554433", date(2001, hoy.month, 9), "956789012"),
            ("Pedro", "Castillo Núñez", "43998877", date(1965, 1, 30), "967890123"),
        ]
        pac = [Paciente.objects.create(nombres=n, apellidos=a, dni=d, fecha_nacimiento=f, telefono=t,
                                       direccion="Av. Los Próceres 123, Lima",
                                       correo=f"{n.lower()}@correo.com") for n, a, d, f, t in datos]

        Antecedente.objects.create(paciente=pac[0], alergias="Penicilina", enfermedades="",
                                   medicamentos="Ninguno")
        Antecedente.objects.create(paciente=pac[1], enfermedades="Hipertensión arterial",
                                   medicamentos="Losartán 50 mg", fuma=True)
        Antecedente.objects.create(paciente=pac[2])

        def cita(p, o, dias, h, motivo, estado):
            return Cita.objects.create(paciente=p, odontologo=o, fecha=hoy + timedelta(days=dias),
                                       hora=time(h, 0), motivo=motivo, estado=estado)

        # Historial atendido
        c1 = cita(pac[0], odo[0], -20, 9, "Dolor en molar inferior", Cita.ATENDIDA)
        c2 = cita(pac[1], odo[2], -35, 11, "Sensibilidad al frío", Cita.ATENDIDA)
        c3 = cita(pac[2], odo[1], -60, 16, "Evaluación de ortodoncia", Cita.ATENDIDA)
        c4 = cita(pac[3], odo[0], -240, 10, "Limpieza dental", Cita.ATENDIDA)
        cita(pac[5], odo[0], -10, 15, "Control", Cita.CANCELADA)
        # Agenda próxima
        cita(pac[0], odo[0], 0, 10, "Control de obturación", Cita.CONFIRMADA)
        cita(pac[4], odo[0], 0, 12, "Primera consulta", Cita.PENDIENTE)
        cita(pac[1], odo[2], 1, 9, "Continuación de endodoncia", Cita.PENDIENTE)
        cita(pac[2], odo[1], 2, 17, "Ajuste de brackets", Cita.PENDIENTE)
        cita(pac[5], odo[0], 4, 11, "Revisión general", Cita.CONFIRMADA)

        d1 = Diagnostico.objects.create(cita=c1, fecha=c1.fecha, descripcion="Caries profunda en pieza 36",
                                        recomendaciones="Obturación con resina y control en 30 días.")
        d2 = Diagnostico.objects.create(cita=c2, fecha=c2.fecha, descripcion="Pulpitis irreversible en pieza 46",
                                        recomendaciones="Tratamiento de conductos.")
        d3 = Diagnostico.objects.create(cita=c3, fecha=c3.fecha, descripcion="Maloclusión clase II",
                                        recomendaciones="Ortodoncia fija por 18 meses.")
        d4 = Diagnostico.objects.create(cita=c4, fecha=c4.fecha, descripcion="Gingivitis leve",
                                        recomendaciones="Profilaxis y uso de hilo dental.")

        t1 = Tratamiento.objects.create(diagnostico=d1, nombre="Obturación con resina", descripcion="Resina en pieza 36",
                                        fecha_inicio=d1.fecha, fecha_fin=d1.fecha, costo=Decimal("180.00"),
                                        estado=Tratamiento.FINALIZADO)
        t2 = Tratamiento.objects.create(diagnostico=d2, nombre="Endodoncia molar", descripcion="Conductos pieza 46",
                                        fecha_inicio=d2.fecha, fecha_fin=hoy - timedelta(days=5),
                                        costo=Decimal("650.00"), estado=Tratamiento.EN_PROCESO)
        t3 = Tratamiento.objects.create(diagnostico=d3, nombre="Ortodoncia fija", descripcion="Brackets metálicos",
                                        fecha_inicio=d3.fecha, fecha_fin=hoy + timedelta(days=480),
                                        costo=Decimal("3200.00"), estado=Tratamiento.EN_PROCESO)
        Tratamiento.objects.create(diagnostico=d4, nombre="Profilaxis", descripcion="Limpieza y destartraje",
                                   fecha_inicio=d4.fecha, fecha_fin=d4.fecha, costo=Decimal("120.00"),
                                   estado=Tratamiento.FINALIZADO)

        Receta.objects.create(diagnostico=d1, medicamento="Ibuprofeno 400 mg", dosis="1 tableta",
                              frecuencia="Cada 8 horas", duracion="3 días", fecha_emision=d1.fecha,
                              indicaciones="Tomar después de los alimentos.")
        Receta.objects.create(diagnostico=d2, medicamento="Amoxicilina 500 mg", dosis="1 cápsula",
                              frecuencia="Cada 8 horas", duracion="7 días", fecha_emision=d2.fecha)

        Pago.objects.create(tratamiento=t1, fecha=t1.fecha_inicio, monto=Decimal("180.00"),
                            metodo="Yape / Plin", comprobante="Boleta", numero_comprobante="B001-000101")
        Pago.objects.create(tratamiento=t2, fecha=t2.fecha_inicio, monto=Decimal("300.00"),
                            metodo="Efectivo", comprobante="Boleta", numero_comprobante="B001-000102")
        Pago.objects.create(tratamiento=t3, fecha=t3.fecha_inicio, monto=Decimal("800.00"),
                            metodo="Tarjeta", comprobante="Factura", numero_comprobante="F001-000045")

        for n, e, caras in [(36, PiezaDental.OBTURADO, "O"), (46, PiezaDental.ENDODONCIA, ""),
                            (18, PiezaDental.AUSENTE, ""), (24, PiezaDental.CARIES, "MO")]:
            PiezaDental.objects.create(paciente=pac[0] if n in (36, 18, 24) else pac[1],
                                       pieza=n, estado=e, caras=caras)

        for cod, nom, cat, uni, st, mn, pr in [
            ("RES-A2", "Resina compuesta A2", "Material de restauración", "Jeringa", 12, 5, "85.00"),
            ("ANE-LID", "Lidocaína 2% con epinefrina", "Anestesia", "Caja", 3, 4, "120.00"),
            ("GUA-M", "Guantes de nitrilo talla M", "Bioseguridad", "Caja", 0, 5, "28.00"),
            ("LIM-K25", "Limas K n.º 25", "Endodoncia", "Paquete", 8, 3, "45.00"),
            ("BRA-MET", "Brackets metálicos Roth", "Ortodoncia", "Paquete", 6, 2, "160.00"),
        ]:
            Insumo.objects.create(codigo=cod, nombre=nom, categoria=cat, unidad=uni, stock=st,
                                  stock_minimo=mn, precio=Decimal(pr),
                                  fecha_vencimiento=hoy + timedelta(days=300))

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
