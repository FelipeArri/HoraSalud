"""DEF-08 (CP-29): el ingreso con RUT de pacientes y tutores limita los intentos (OWASP A04/A07)."""
import json
from io import StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import limite_intentos, passkeys
from .autenticador_simulado import AutenticadorSimulado
from .models import RegistroAuditoria, Usuario

RUT_NO_INSCRITO = '11.111.111-1'


@override_settings(WEBAUTHN_RP_IDS=['localhost'], WEBAUTHN_ORIGENES=['http://localhost:8000'],
                   HORASALUD_INGRESO_DEMO=False)
class LimiteIntentosTests(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        cache.clear()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        call_command('cargar_datos_demo', stdout=StringIO())
        self.paciente = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PACIENTE).order_by('rut').first()
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)

    def post_json(self, nombre, cuerpo='{}'):
        return self.client.post(reverse(nombre), data=cuerpo, content_type='application/json')

    def enrolar(self, autenticador):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        self.post_json('passkey_registro_verificar', autenticador.registrar(opciones))
        self.client.post(reverse('salir'))

    def intentar_con(self, autenticador):
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        respuesta = self.post_json('passkey_ingreso_opciones')
        if respuesta.status_code != 200:
            return respuesta
        return self.post_json('passkey_ingreso_verificar', autenticador.firmar(respuesta.json()['opciones']))

    # --- por origen: probar RUT tras RUT ---
    def test_origen_se_bloquea_tras_10_rut_no_encontrados(self):
        for _ in range(limite_intentos.MAX_RUT_POR_ORIGEN):
            self.assertContains(self.client.post(reverse('ingresar'), {'rut': RUT_NO_INSCRITO}),
                                'No encontramos una inscripción activa')
        # Ni siquiera un RUT inscrito pasa mientras dura el bloqueo
        respuesta = self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertContains(respuesta, 'demasiados intentos')
        self.assertNotIn('rut_pendiente', self.client.session)

    def test_bloqueo_por_origen_tambien_aplica_al_enrolamiento(self):
        for _ in range(limite_intentos.MAX_RUT_POR_ORIGEN):
            self.client.post(reverse('enrolar'), {'rut': RUT_NO_INSCRITO, 'codigo': '1234-5678'})
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        respuesta = self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        self.assertContains(respuesta, 'demasiados intentos')

    def test_rut_inscrito_no_suma_intentos(self):
        for _ in range(limite_intentos.MAX_RUT_POR_ORIGEN + 2):
            self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertFalse(limite_intentos.origen_bloqueado(self.client.get(reverse('ingresar')).wsgi_request))

    # --- por RUT: huellas rechazadas ---
    def test_rut_se_bloquea_tras_5_huellas_rechazadas_y_queda_auditado(self):
        propia = AutenticadorSimulado()
        self.enrolar(propia)
        for _ in range(limite_intentos.MAX_HUELLAS_POR_RUT - 1):
            self.assertEqual(self.intentar_con(AutenticadorSimulado()).status_code, 400)
        quinto = self.intentar_con(AutenticadorSimulado())
        self.assertEqual(quinto.status_code, 429)
        # Mientras dura el bloqueo, ni la huella correcta sirve
        respuesta = self.intentar_con(propia)
        self.assertEqual(respuesta.status_code, 429)
        self.assertIn('bloqueado', json.loads(respuesta.content)['error'])
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.Accion.INGRESO_BLOQUEADO, objetivo=self.paciente).exists())

    def test_ingreso_correcto_reinicia_el_contador(self):
        propia = AutenticadorSimulado()
        self.enrolar(propia)
        for _ in range(limite_intentos.MAX_HUELLAS_POR_RUT - 1):
            self.intentar_con(AutenticadorSimulado())
        self.assertEqual(self.intentar_con(propia).status_code, 200)
        self.client.post(reverse('salir'))
        self.assertEqual(self.intentar_con(AutenticadorSimulado()).status_code, 400)  # vuelve a contar desde 1
