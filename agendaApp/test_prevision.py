"""Pruebas de B-19 · RN-16: un cambio de previsión deja al paciente No vigente y cancela sus horas."""
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacionApp.models import Paciente, Usuario
from fonasaSimuladoApp.models import PersonaFonasa
from notificacionesApp.models import RegistroNotificacion

from . import prevision, servicios
from .models import BloqueHorario, Hora


class FonasaFalso:
    """Reemplaza al AdapterFonasa: responde la previsión que se le indique y cuenta las consultas."""

    def __init__(self, prevision_respuesta='fonasa', tramo='B'):
        self.respuesta, self.tramo, self.consultas = prevision_respuesta, tramo, 0

    def consultar_prevision(self, rut):
        self.consultas += 1
        es_fonasa = self.respuesta == 'fonasa'
        return {'prevision': self.respuesta, 'tramo': self.tramo if es_fonasa else '', 'vigente': True}


class PrevisionVigenteTests(TestCase):
    databases = {'default', 'fonasa'}  # tambien consulta el padron FONASA simulado

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.paciente = Paciente.objects.filter(horas__estado__in=[Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA]) \
            .select_related('usuario').first()

    def servicios(self, respuesta, tramo='B'):
        self.fonasa = FonasaFalso(respuesta, tramo)
        return (None, self.fonasa)

    def test_consulta_reciente_no_vuelve_a_consultar(self):
        self.paciente.prevision_consultada_en = timezone.now() - timedelta(days=5)
        self.paciente.save()
        prevision.revalidar(self.paciente, self.servicios('isapre'))
        self.assertEqual(self.fonasa.consultas, 0)

    def test_consulta_vencida_si_consulta(self):
        self.paciente.prevision_consultada_en = timezone.now() - timedelta(days=31)
        self.paciente.save()
        prevision.revalidar(self.paciente, self.servicios('fonasa', 'C'))
        self.assertEqual(self.fonasa.consultas, 1)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.tramo, 'C')

    def test_cambio_a_isapre_cancela_horas_futuras_y_avisa(self):
        futuras = list(prevision.horas_futuras(self.paciente))
        bloques = [h.bloque_id for h in futuras]
        resultado = prevision.revalidar(self.paciente, self.servicios('isapre'), forzar=True)
        self.assertTrue(resultado.cambio_a_no_vigente)
        self.assertEqual(resultado.horas_canceladas, len(futuras))
        self.paciente.refresh_from_db()
        self.assertEqual((self.paciente.estado_inscripcion, self.paciente.prevision), ('no_vigente', 'isapre'))
        for hora in Hora.objects.filter(pk__in=[h.pk for h in futuras]):
            self.assertEqual(hora.estado, Hora.Estado.CANCELADA)
            self.assertEqual(hora.motivo_cancelacion, 'CESFAM: cambio de previsión (ISAPRE)')
        # Los bloques quedan libres para otras personas
        self.assertFalse(BloqueHorario.objects.filter(pk__in=bloques).exclude(estado='disponible').exists())
        self.assertEqual(RegistroNotificacion.objects.filter(hora__paciente=self.paciente).count(), len(futuras))

    def test_dipreca_y_capredena_tambien(self):
        for respuesta in ['dipreca', 'capredena']:
            paciente = Paciente.objects.filter(estado_inscripcion='vigente').exclude(pk=self.paciente.pk).first()
            prevision.revalidar(paciente, self.servicios(respuesta), forzar=True)
            paciente.refresh_from_db()
            self.assertEqual((paciente.estado_inscripcion, paciente.prevision), ('no_vigente', respuesta))

    def test_horas_pasadas_o_atendidas_no_se_tocan(self):
        hora = prevision.horas_futuras(self.paciente).first()
        hora.estado = Hora.Estado.ATENDIDA
        hora.save()
        prevision.revalidar(self.paciente, self.servicios('isapre'), forzar=True)
        hora.refresh_from_db()
        self.assertEqual(hora.estado, Hora.Estado.ATENDIDA)

    def test_no_vigente_no_puede_reservar(self):
        prevision.dejar_no_vigente(self.paciente, 'isapre')
        bloque = BloqueHorario.objects.filter(estado='disponible', agenda__fecha__gt=timezone.localdate()).first()
        with self.assertRaises(servicios.ReglaNegocioError):
            servicios.reservar_hora(self.paciente, bloque.pk)

    def test_pantallas_del_paciente_no_vigente(self):
        prevision.dejar_no_vigente(self.paciente, 'isapre')
        self.client.force_login(self.paciente.usuario)
        inicio = self.client.get(reverse('mi_inicio'))
        self.assertContains(inicio, 'No puedes pedir horas por la aplicación')
        self.assertNotContains(inicio, 'Pedir una hora')
        respuesta = self.client.get(reverse('pedir_especialidad'), follow=True)
        self.assertRedirects(respuesta, reverse('mi_inicio'))
        self.assertContains(respuesta, 'ISAPRE')

    def test_some_reactiva_solo_si_volvio_a_fonasa(self):
        prevision.dejar_no_vigente(self.paciente, 'isapre')
        self.assertFalse(prevision.reactivar(self.paciente, self.servicios('isapre')))
        self.assertTrue(prevision.reactivar(self.paciente, self.servicios('fonasa', 'A')))
        self.paciente.refresh_from_db()
        self.assertEqual((self.paciente.estado_inscripcion, self.paciente.tramo), ('vigente', 'A'))

    def test_panel_some_no_vigentes(self):
        prevision.dejar_no_vigente(self.paciente, 'capredena')
        self.client.force_login(Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO))
        self.assertContains(self.client.get(reverse('some_no_vigentes')), self.paciente.usuario.rut)
        self.client.force_login(self.paciente.usuario)
        self.assertRedirects(self.client.get(reverse('some_no_vigentes')), reverse('inicio'))


class ComandosTests(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())

    def test_cambio_en_el_padron_y_revision_mensual(self):
        # En el padrón FONASA simulado, Luis se cambia a ISAPRE (como se haría en /admin/)
        PersonaFonasa.objects.filter(rut='30000008-8').update(prevision='ISAPRE', tramo='')
        salida = StringIO()
        call_command('revisar_prevision', stdout=salida)
        paciente = Paciente.objects.get(usuario__rut='30000008-8')
        self.assertEqual((paciente.estado_inscripcion, paciente.prevision), ('no_vigente', 'isapre'))
        self.assertIn('Pasaron a No vigente: 1', salida.getvalue())
        # Los demás pacientes demo siguen con FONASA en el padrón
        self.assertEqual(Paciente.objects.filter(estado_inscripcion='no_vigente').count(), 1)
