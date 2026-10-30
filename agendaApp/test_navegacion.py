"""Pruebas de reserva, cancelacion y panel SOME (RF-02, RF-05, RN-01 a RN-05, RN-07)."""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacionApp.models import Paciente, Usuario

from . import servicios
from .models import BloqueHorario, Especialidad, Hora


class ReservaTests(TestCase):
    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        # Dos pacientes sin horas para partir limpio
        self.paciente, self.otro = Paciente.objects.select_related('usuario')[:2]
        Hora.objects.filter(paciente__in=[self.paciente, self.otro]).delete()
        self.client.force_login(self.paciente.usuario)
        self.especialidad = Especialidad.objects.get(nombre='Medicina General')
        self.bloque = servicios.bloques_reservables(self.especialidad)[0]

    def test_flujo_completo_de_reserva_en_tres_pasos(self):
        self.assertContains(self.client.get(reverse('pedir_especialidad')), 'Medicina General')
        self.assertContains(self.client.get(reverse('pedir_bloque', args=[self.especialidad.pk])),
                            f'{self.bloque.hora_inicio:%H:%M}')
        respuesta = self.client.post(reverse('pedir_confirmar', args=[self.bloque.pk]))
        hora = Hora.objects.get(paciente=self.paciente)
        self.assertRedirects(respuesta, reverse('hora_lista', args=[hora.pk]))
        self.assertEqual(BloqueHorario.objects.get(pk=self.bloque.pk).estado, BloqueHorario.Estado.RESERVADO)

    def test_bloque_tomado_muestra_mensaje(self):
        servicios.reservar_hora(self.otro, self.bloque.pk)
        respuesta = self.client.post(reverse('pedir_confirmar', args=[self.bloque.pk]), follow=True)
        self.assertContains(respuesta, 'acaba de ser tomado')

    def test_rn01_una_hora_vigente_por_especialidad(self):
        servicios.reservar_hora(self.paciente, self.bloque.pk)
        segundo = servicios.bloques_reservables(self.especialidad)[0]
        with self.assertRaises(servicios.ReglaNegocioError):
            servicios.reservar_hora(self.paciente, segundo.pk)

    def test_rn03_fuera_del_horizonte_se_rechaza(self):
        self.bloque.agenda.fecha = timezone.localdate() + timedelta(days=45)
        self.bloque.agenda.save()
        with self.assertRaises(servicios.ReglaNegocioError):
            servicios.reservar_hora(self.paciente, self.bloque.pk)

    def test_cancelar_con_motivo_libera_el_bloque(self):
        hora = servicios.reservar_hora(self.paciente, self.bloque.pk)
        respuesta = self.client.post(reverse('cancelar_hora', args=[hora.pk]), {'motivo': 'Ya me siento mejor'})
        self.assertRedirects(respuesta, reverse('mis_horas'))
        hora.refresh_from_db()
        self.assertEqual(hora.estado, Hora.Estado.CANCELADA)
        self.assertEqual(hora.motivo_cancelacion, 'Paciente: Ya me siento mejor')

    def test_rn05_cancelar_sin_motivo_se_rechaza(self):
        hora = servicios.reservar_hora(self.paciente, self.bloque.pk)
        self.client.post(reverse('cancelar_hora', args=[hora.pk]), {'motivo': ''})
        hora.refresh_from_db()
        self.assertEqual(hora.estado, Hora.Estado.RESERVADA)

    def test_rn04_no_se_cancela_a_menos_de_2_horas(self):
        hora = servicios.reservar_hora(self.paciente, self.bloque.pk)
        casi = servicios.inicio_bloque(hora.bloque) - timedelta(minutes=30)
        with mock.patch('django.utils.timezone.localtime', return_value=casi):
            with self.assertRaises(servicios.ReglaNegocioError):
                servicios.cancelar_hora(hora, 'Otro motivo')

    def test_rn07_no_se_ve_la_hora_de_otro_paciente(self):
        ajena = Hora.objects.exclude(paciente=self.paciente).first()
        self.assertEqual(self.client.get(reverse('cancelar_hora', args=[ajena.pk])).status_code, 404)

    def test_confirmar_asistencia(self):
        hora = servicios.reservar_hora(self.paciente, self.bloque.pk)
        self.client.post(reverse('confirmar_asistencia', args=[hora.pk]))
        hora.refresh_from_db()
        self.assertEqual(hora.estado, Hora.Estado.CONFIRMADA)


class SomeTests(TestCase):
    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.client.force_login(Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO))
        self.hora = Hora.objects.filter(estado=Hora.Estado.RESERVADA).select_related('bloque__agenda').first()

    def test_nomina_muestra_rut_y_ficha(self):
        dia = self.hora.bloque.agenda.fecha.isoformat()
        respuesta = self.client.get(reverse('some_nomina'), {'dia': dia})
        self.assertContains(respuesta, self.hora.paciente.usuario.rut)
        self.assertContains(respuesta, self.hora.paciente.ficha_clinica_id)

    def test_marcar_atendida(self):
        self.client.post(reverse('some_accion', args=[self.hora.pk, 'atendida']))
        self.hora.refresh_from_db()
        self.assertEqual(self.hora.estado, Hora.Estado.ATENDIDA)

    def test_no_show_solo_despues_de_20_minutos(self):
        # RF-05
        inicio = servicios.inicio_bloque(self.hora.bloque)
        with mock.patch('django.utils.timezone.localtime', return_value=inicio + timedelta(minutes=10)):
            self.assertFalse(servicios.puede_marcar_no_show(self.hora))
        with mock.patch('django.utils.timezone.localtime', return_value=inicio + timedelta(minutes=21)):
            servicios.marcar_no_show(self.hora)
        self.assertEqual(Hora.objects.get(pk=self.hora.pk).estado, Hora.Estado.NO_SHOW)


class PantallaSalaTests(TestCase):
    def test_pantalla_publica_sin_datos_personales(self):
        # RN-10 y RN-12
        call_command('cargar_datos_demo', stdout=StringIO())
        respuesta = self.client.get(reverse('sala_espera'))
        self.assertEqual(respuesta.status_code, 200)
        for paciente in Paciente.objects.select_related('usuario'):
            self.assertNotContains(respuesta, paciente.usuario.rut)
            self.assertNotContains(respuesta, paciente.usuario.last_name)
