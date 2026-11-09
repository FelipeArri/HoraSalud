"""
CP-17 · RF-01 (integración, negativo): el sistema clínico o FONASA no responde.

Resultado esperado: un mensaje controlado, sin error interno (500) y sin acciones
a medias (no se entrega código, no se cambia el estado del paciente).
"""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacionApp.models import CodigoEnrolamiento, Paciente, Usuario

from .models import BloqueHorario, Hora

CAIDO = mock.patch('fonasaSimuladoApp.clientes.ClienteFonasaBD.obtener',
                   side_effect=ConnectionError('FONASA no responde'))
CLINICO_CAIDO = mock.patch('fonasaSimuladoApp.clientes.ClienteInscripcionBD.obtener',
                           side_effect=TimeoutError('Sistema clínico sin respuesta'))
AVISO = 'no responde'


class ServicioExternoCaidoTests(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.client.raise_request_exception = False  # ver lo que vería la persona (500 o mensaje)
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.paciente = Paciente.objects.select_related('usuario').first()

    def test_some_entrega_codigo_con_sistema_clinico_caido(self):
        self.client.force_login(self.some)
        with CLINICO_CAIDO:
            consulta = self.client.get(reverse('some_enrolar'), {'rut': self.paciente.usuario.rut})
            entrega = self.client.post(reverse('some_enrolar'), {'rut': self.paciente.usuario.rut,
                                                                 'cedula_validada': 'si', 'reemplazar': 'si'})
        self.assertContains(consulta, AVISO)
        self.assertContains(entrega, AVISO)
        self.assertFalse(CodigoEnrolamiento.objects.filter(usuario=self.paciente.usuario).exists())

    def test_some_entrega_codigo_con_fonasa_caido(self):
        self.client.force_login(self.some)
        with CAIDO:
            respuesta = self.client.get(reverse('some_enrolar'), {'rut': self.paciente.usuario.rut})
        self.assertContains(respuesta, AVISO)

    def test_some_tutores_con_fonasa_caido(self):
        self.client.force_login(self.some)
        with CAIDO:
            respuesta = self.client.get(reverse('some_tutores'), {'rut': self.paciente.usuario.rut})
        self.assertContains(respuesta, AVISO)

    def test_paciente_reserva_aunque_fonasa_no_responda(self):
        # Su última consulta tiene más de 30 días: toca revalidar, pero FONASA está caído.
        # Se mantiene el último estado conocido (vigente) y se vuelve a intentar en la próxima reserva.
        self.paciente.prevision_consultada_en = timezone.now() - timedelta(days=31)
        self.paciente.save()
        Hora.objects.filter(paciente=self.paciente).update(estado=Hora.Estado.CANCELADA)
        bloque = (BloqueHorario.objects.filter(estado='disponible', tipo_cupo='programado',
                                               agenda__fecha__gt=timezone.localdate(),
                                               agenda__fecha__lte=timezone.localdate() + timedelta(days=25))
                  .filter(agenda__profesional__sector__isnull=True).first())
        self.client.force_login(self.paciente.usuario)
        with CAIDO:
            respuesta = self.client.post(reverse('pedir_confirmar', args=[bloque.pk]))
        self.assertNotEqual(respuesta.status_code, 500)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.estado_inscripcion, Paciente.Estado.VIGENTE)
        self.assertLess(self.paciente.prevision_consultada_en, timezone.now() - timedelta(days=30))  # reintenta
        self.assertTrue(Hora.objects.filter(paciente=self.paciente, bloque=bloque).exists())

    def test_some_reactivar_con_fonasa_caido(self):
        from . import prevision
        prevision.dejar_no_vigente(self.paciente, 'isapre')
        self.client.force_login(self.some)
        with CAIDO:
            respuesta = self.client.post(reverse('some_no_vigentes'), {'paciente': self.paciente.pk}, follow=True)
        self.assertContains(respuesta, AVISO)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.estado_inscripcion, Paciente.Estado.NO_VIGENTE)
