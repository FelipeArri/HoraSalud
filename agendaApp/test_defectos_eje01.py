"""Pruebas de los defectos hallados en la ejecución EJE-01 (02-11-2026).

DEF-06 (RF-02, CP-04 y CP-05): cada paciente ve solo las agendas de su sector.
DEF-07 (RN-11, CP-20 y CP-33): la reserva, la cancelación y el No-Show quedan en el registro de auditoría.
"""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacionApp.models import Paciente, Profesional, RegistroAuditoria, Sector, Usuario

from . import prevision, servicios
from .models import Especialidad, Hora

Accion = RegistroAuditoria.Accion


class Base(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.especialidad = Especialidad.objects.get(nombre='Medicina General')
        self.prof = Profesional.objects.get(especialidad=self.especialidad)
        self.sector_1, self.sector_2 = Sector.objects.order_by('nombre')[:2]
        self.paciente = Paciente.objects.select_related('usuario').filter(sector=self.sector_1).first()
        Hora.objects.filter(paciente=self.paciente).delete()
        self.paciente.prevision_consultada_en = timezone.now()  # no consultar FONASA en cada prueba
        self.paciente.save()

    def asignar_sector(self, sector):
        self.prof.sector = sector
        self.prof.save()


class SectorTests(Base):
    """DEF-06."""

    def test_no_ve_agendas_de_otro_sector(self):
        self.asignar_sector(self.sector_2)
        self.assertEqual(servicios.bloques_reservables(self.especialidad, self.paciente), [])

    def test_ve_agendas_de_su_sector(self):
        self.asignar_sector(self.sector_1)
        libres = servicios.bloques_reservables(self.especialidad, self.paciente)
        self.assertTrue(libres)
        self.assertTrue(all(b.agenda.profesional_id == self.prof.pk for b in libres))

    def test_profesional_sin_sector_atiende_a_todos(self):
        self.asignar_sector(None)
        self.assertTrue(servicios.bloques_reservables(self.especialidad, self.paciente))

    def test_no_puede_reservar_un_bloque_de_otro_sector(self):
        bloque = servicios.bloques_reservables(self.especialidad, self.paciente)[0]
        self.asignar_sector(self.sector_2)
        with self.assertRaisesMessage(servicios.ReglaNegocioError, 'otro sector'):
            servicios.reservar_hora(self.paciente, bloque.pk)
        self.assertFalse(Hora.objects.filter(paciente=self.paciente).exists())

    def test_paciente_sin_sector_ve_solo_profesionales_sin_sector(self):
        self.paciente.sector = None
        self.paciente.save()
        self.asignar_sector(self.sector_1)
        self.assertEqual(servicios.bloques_reservables(self.especialidad, self.paciente), [])

    def test_pantalla_pedir_hora_no_muestra_otro_sector(self):
        self.asignar_sector(self.sector_2)
        self.client.force_login(self.paciente.usuario)
        respuesta = self.client.get(reverse('pedir_bloque', args=[self.especialidad.pk]))
        self.assertEqual(respuesta.context['bloques'], [])


class AuditoriaHorasTests(Base):
    """DEF-07."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.paciente.usuario)
        self.bloque = servicios.bloques_reservables(self.especialidad, self.paciente)[0]

    def reservar_por_la_app(self):
        self.client.post(reverse('pedir_confirmar', args=[self.bloque.pk]))
        return Hora.objects.get(paciente=self.paciente)

    def test_reserva_queda_registrada(self):
        self.reservar_por_la_app()
        registro = RegistroAuditoria.objects.get(accion=Accion.RESERVA)
        self.assertEqual(registro.actor, self.paciente.usuario)
        self.assertEqual(registro.objetivo, self.paciente.usuario)
        self.assertEqual(registro.ip, '127.0.0.1')
        self.assertIn(f'{self.bloque.hora_inicio:%H:%M}', registro.detalle)

    def test_cancelacion_queda_registrada_sin_el_motivo(self):
        hora = self.reservar_por_la_app()
        self.client.post(reverse('cancelar_hora', args=[hora.pk]), {'motivo': 'Ya me siento mejor'})
        registro = RegistroAuditoria.objects.get(accion=Accion.CANCELACION)
        self.assertEqual(registro.actor, self.paciente.usuario)
        self.assertNotIn('mejor', registro.detalle)  # el motivo va cifrado en la hora, no se copia

    def test_no_show_y_atendida_quedan_registrados_con_el_funcionario(self):
        hora = self.reservar_por_la_app()
        otra = Hora.objects.filter(estado=Hora.Estado.RESERVADA).exclude(pk=hora.pk).first()
        some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(some)
        despues = servicios.inicio_bloque(hora.bloque) + timedelta(minutes=25)
        with mock.patch('django.utils.timezone.localtime', return_value=despues):
            self.client.post(reverse('some_accion', args=[hora.pk, 'no-show']))
        self.client.post(reverse('some_accion', args=[otra.pk, 'atendida']))
        no_show = RegistroAuditoria.objects.get(accion=Accion.NO_SHOW)
        self.assertEqual((no_show.actor, no_show.objetivo), (some, self.paciente.usuario))
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.ATENDIDA, actor=some).exists())

    def test_cancelacion_automatica_por_prevision_queda_como_sistema(self):
        self.reservar_por_la_app()
        prevision.dejar_no_vigente(self.paciente, 'isapre')
        registro = RegistroAuditoria.objects.get(accion=Accion.CANCELACION)
        self.assertIsNone(registro.actor)
        self.assertIn('RN-16', registro.detalle)
