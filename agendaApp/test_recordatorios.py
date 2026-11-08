"""
Pruebas de B-23: recordatorio de la hora el día anterior (aviso push o dentro de la app).

El reloj se fija con mock en AHORA (mañana a las 10:00); "mañana" para el
sistema es entonces pasado mañana en el calendario real.
"""
import json
from datetime import datetime, time, timedelta
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from autenticacionApp import privacidad
from autenticacionApp.models import Paciente, Profesional, Usuario
from notificacionesApp.models import RegistroNotificacion, SuscripcionPush

from . import prevision, recordatorios
from .models import Agenda, BloqueHorario, Especialidad, Hora

HOY = timezone.localdate()  # fecha real, tomada antes de fijar el reloj


def a_las(hora, minuto=0, dias=1):
    return timezone.make_aware(datetime.combine(HOY + timedelta(days=dias), time(hora, minuto)))


AHORA = a_las(10)


@override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=False, VAPID_PUBLIC_KEY='', VAPID_PRIVATE_KEY='')
class Base(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        self.reloj = mock.patch('django.utils.timezone.now', return_value=AHORA)
        self.reloj.start()
        self.addCleanup(self.reloj.stop)
        self.especialidad = Especialidad.objects.create(nombre='Nutrición', tipo=Especialidad.Tipo.PROGRAMA)
        prof = Usuario.objects.create(username='nutri', rut='31000002-3', tipo_usuario=Usuario.Tipo.PROFESIONAL)
        self.prof = Profesional.objects.create(usuario=prof, especialidad=self.especialidad, box_atencion='3')
        usuario = Usuario.objects.create(username='rosa', rut='30600001-8', first_name='Rosa', last_name='Prueba')
        privacidad.registrar(usuario, True)
        self.paciente = Paciente.objects.create(usuario=usuario, prevision_consultada_en=AHORA)

    def hora(self, dias_desde_ahora=1, a_la=time(9, 40), estado=Hora.Estado.RESERVADA):
        fecha = timezone.localtime(AHORA).date() + timedelta(days=dias_desde_ahora)
        agenda, _ = Agenda.objects.get_or_create(especialidad=self.especialidad, profesional=self.prof, fecha=fecha)
        bloque = BloqueHorario.objects.create(agenda=agenda, hora_inicio=a_la,
                                              hora_fin=(datetime.combine(fecha, a_la) + timedelta(minutes=20)).time())
        return Hora.objects.create(bloque=bloque, paciente=self.paciente, estado=estado)


class RecordatorioTests(Base):
    def test_se_envia_una_sola_vez_a_las_horas_de_manana(self):
        hora = self.hora()
        self.assertEqual(recordatorios.enviar_recordatorios(), 1)
        self.assertEqual(recordatorios.enviar_recordatorios(), 0)  # no se repite
        hora.refresh_from_db()
        self.assertEqual(hora.recordatorio_enviado_en, AHORA)
        aviso = RegistroNotificacion.objects.get(hora=hora)
        # sin avisos activados: queda visible dentro de HoraSalud (gratis)
        self.assertEqual((aviso.canal, aviso.estado), ('app', 'enviada'))

    def test_solo_horas_vigentes_de_manana(self):
        self.hora(dias_desde_ahora=2)                                  # pasado mañana
        self.hora(dias_desde_ahora=1, a_la=time(11), estado=Hora.Estado.CANCELADA)
        self.hora(dias_desde_ahora=0, a_la=time(15))                   # hoy
        self.assertEqual(recordatorios.enviar_recordatorios(), 0)

    def test_solo_de_8_a_20(self):
        self.hora()
        self.assertEqual(recordatorios.enviar_recordatorios(a_las(21)), 0)
        self.assertEqual(recordatorios.enviar_recordatorios(a_las(7, 59)), 0)
        self.assertEqual(recordatorios.enviar_recordatorios(a_las(8)), 1)

    def test_texto_sin_datos_de_salud(self):
        reservada = self.hora()
        confirmada = self.hora(a_la=time(12), estado=Hora.Estado.CONFIRMADA)
        self.assertIn('Confirma que irás', recordatorios.mensaje_recordatorio(reservada))
        self.assertIn('Si no puedes ir', recordatorios.mensaje_recordatorio(confirmada))
        texto = recordatorios.mensaje_recordatorio(reservada)
        self.assertIn('09:40', texto)
        self.assertNotIn('Nutrición', texto)  # Ley 19.628

    @override_settings(VAPID_PUBLIC_KEY='publica', VAPID_PRIVATE_KEY='privada')
    @mock.patch('pywebpush.webpush')
    def test_llega_por_push_al_paciente_y_a_su_tutor(self, webpush):
        tutor = Usuario.objects.create(username='tutor', rut='32200001-K', tipo_usuario=Usuario.Tipo.TUTOR)
        self.paciente.tutor = tutor
        self.paciente.save()
        for usuario, fin in ((self.paciente.usuario, 'a'), (tutor, 'b')):
            SuscripcionPush.objects.create(usuario=usuario, endpoint=f'https://fcm.googleapis.com/fcm/send/{fin}',
                                           p256dh='k', auth='a')
        hora = self.hora()
        recordatorios.enviar_recordatorios()
        self.assertEqual(webpush.call_count, 2)
        self.assertEqual(json.loads(webpush.call_args.kwargs['data'])['url'], f'/mis-horas/{hora.pk}/')
        self.assertEqual(RegistroNotificacion.objects.get(hora=hora).canal, 'push')

    def test_tambien_se_ve_dentro_de_la_app(self):
        self.hora()
        self.client.force_login(self.paciente.usuario)
        self.assertContains(self.client.get(reverse('mi_inicio')), 'Mañana tienes hora a las 09:40')

    def test_la_pantalla_de_reserva_ya_no_promete_de_mas(self):
        hora = self.hora(dias_desde_ahora=5)
        self.client.force_login(self.paciente.usuario)
        pagina = self.client.get(reverse('hora_lista', args=[hora.pk]))
        self.assertContains(pagina, 'El día anterior te enviaremos un recordatorio')

    def test_no_vigentes_cuenta_horas_no_avisos(self):
        hora = self.hora()
        recordatorios.enviar_recordatorios()  # la hora ya tiene su recordatorio registrado
        prevision.dejar_no_vigente(self.paciente, Paciente.Prevision.ISAPRE)  # RN-16: se cancela y se avisa
        some = Usuario.objects.create(username='some', rut='32100001-4', tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(some)
        pagina = self.client.get(reverse('some_no_vigentes'))
        self.assertContains(pagina, '1 hora(s) cancelada(s)')
        self.assertEqual(Hora.objects.get(pk=hora.pk).estado, Hora.Estado.CANCELADA)


class TareasAutomaticasTests(Base):
    def test_comando_tareas(self):
        self.hora()
        salida = mock.Mock()
        call_command('tareas_horasalud', stdout=salida)
        self.assertIn('recordatorios enviados: 1', salida.write.call_args.args[0])

    @override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=True)
    def test_las_visitas_envian_los_recordatorios(self):
        from django.core.cache import cache
        cache.clear()
        hora = self.hora()
        self.client.get(reverse('ayuda'))
        hora.refresh_from_db()
        self.assertIsNotNone(hora.recordatorio_enviado_en)
