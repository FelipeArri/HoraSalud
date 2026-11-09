"""
Pruebas de CC-19: segundo factor (MFA) para el personal del CESFAM (RNF-SEC02, OWASP A07).

Usan el AutenticadorSimulado: la firma criptográfica se verifica de verdad, sin un teléfono.
"""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import segundo_factor
from .autenticador_simulado import AutenticadorSimulado
from .models import CredencialPasskey, RegistroAuditoria, Usuario

Accion = RegistroAuditoria.Accion
CLAVE = 'Clave-Personal-2026'


@override_settings(HORASALUD_MFA_PERSONAL=True, HORASALUD_INGRESO_DEMO=False,
                   WEBAUTHN_RP_IDS=['localhost'], WEBAUTHN_ORIGENES=['http://localhost:8000'])
class SegundoFactorTests(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        cache.clear()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        call_command('cargar_datos_demo', stdout=StringIO())
        self.some = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO).first()
        self.some.set_password(CLAVE)
        self.some.debe_cambiar_clave = False
        self.some.last_login = None  # recién entregada en persona: puede registrar su dispositivo
        self.some.save()

    # --- utilidades ---
    def post_json(self, nombre, cuerpo='{}'):
        return self.client.post(reverse(nombre), data=cuerpo, content_type='application/json')

    def clave(self, clave=CLAVE):
        return self.client.post(reverse('personal_ingresar'), {'rut': self.some.rut, 'clave': clave})

    def registrar(self, autenticador):
        opciones = self.post_json('mfa_registro_opciones').json()['opciones']
        return self.post_json('mfa_registro_verificar', autenticador.registrar(opciones))

    def confirmar(self, autenticador):
        opciones = self.post_json('mfa_ingreso_opciones').json()['opciones']
        return self.post_json('mfa_ingreso_verificar', autenticador.firmar(opciones))

    def con_dispositivo(self):
        """Deja al funcionario con un dispositivo registrado y la sesión cerrada."""
        autenticador = AutenticadorSimulado()
        self.clave()
        self.assertEqual(self.registrar(autenticador).status_code, 200)
        self.client.post(reverse('salir'))
        return autenticador

    def en_sesion(self):
        return '_auth_user_id' in self.client.session

    # --- la clave sola no basta ---
    def test_la_clave_correcta_no_abre_sesion_y_pide_el_segundo_factor(self):
        respuesta = self.clave()
        self.assertRedirects(respuesta, reverse('personal_segundo_factor'), fetch_redirect_response=False)
        self.assertFalse(self.en_sesion())
        # Sin el segundo factor no se entra a ninguna pantalla del personal
        self.assertNotEqual(self.client.get(reverse('some_nomina')).status_code, 200)

    def test_primer_ingreso_registra_el_dispositivo_y_abre_sesion(self):
        self.clave()
        respuesta = self.registrar(AutenticadorSimulado())
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertEqual(respuesta.json()['destino'], reverse('some_nomina'))
        self.assertTrue(self.en_sesion())
        credencial = CredencialPasskey.objects.get(usuario=self.some)
        self.assertGreater(len(bytes(credencial.clave_publica)), 0)  # solo la clave pública
        ingreso = RegistroAuditoria.objects.filter(accion=Accion.INGRESO, actor=self.some).latest('fecha')
        self.assertIn('registró su passkey', ingreso.descripcion)

    def test_ingreso_normal_con_clave_y_dispositivo(self):
        autenticador = self.con_dispositivo()
        self.clave()
        respuesta = self.confirmar(autenticador)
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertTrue(self.en_sesion())
        self.assertEqual(self.client.get(reverse('some_nomina')).status_code, 200)
        ingreso = RegistroAuditoria.objects.filter(accion=Accion.INGRESO, actor=self.some).latest('fecha')
        self.assertIn('dos factores', ingreso.descripcion)

    def test_dispositivo_de_otra_persona_no_sirve(self):
        self.con_dispositivo()
        self.clave()
        respuesta = self.confirmar(AutenticadorSimulado())  # otro dispositivo, no registrado
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.en_sesion())

    def test_sin_clave_no_hay_segundo_factor(self):
        self.con_dispositivo()
        self.assertEqual(self.post_json('mfa_ingreso_opciones').status_code, 403)
        self.assertEqual(self.post_json('mfa_registro_opciones').status_code, 403)

    def test_clave_robada_no_permite_registrar_un_dispositivo_nuevo(self):
        """Un atacante con la clave de uso diario no puede agregar su propio dispositivo."""
        self.con_dispositivo()  # ya entró una vez: last_login quedó guardado
        self.clave()
        self.assertEqual(self.post_json('mfa_registro_opciones').status_code, 403)
        self.assertEqual(CredencialPasskey.objects.filter(usuario=self.some).count(), 1)

    def test_clave_temporal_permite_registrar_dispositivo_nuevo_y_obliga_a_cambiar_clave(self):
        self.con_dispositivo()
        self.some.refresh_from_db()
        self.some.set_password(CLAVE)
        self.some.debe_cambiar_clave = True  # el Administrador entregó una clave temporal
        self.some.save()
        self.clave()
        respuesta = self.registrar(AutenticadorSimulado())
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertEqual(respuesta.json()['destino'], reverse('personal_cambiar_clave'))
        self.assertEqual(CredencialPasskey.objects.filter(usuario=self.some).count(), 2)

    def test_el_paso_dos_vence_a_los_5_minutos(self):
        self.con_dispositivo()
        self.clave()
        despues = timezone.now() + segundo_factor.VIGENCIA + timedelta(seconds=1)
        with mock.patch('autenticacionApp.segundo_factor.timezone.now', return_value=despues):
            self.assertEqual(self.post_json('mfa_ingreso_opciones').status_code, 403)
            self.assertRedirects(self.client.get(reverse('personal_segundo_factor')),
                                 reverse('personal_ingresar'), fetch_redirect_response=False)

    def test_cinco_dispositivos_rechazados_bloquean(self):
        self.con_dispositivo()
        self.clave()
        for _ in range(5):
            opciones = self.post_json('mfa_ingreso_opciones')
            if opciones.status_code != 200:
                break
            self.post_json('mfa_ingreso_verificar', AutenticadorSimulado().firmar(opciones.json()['opciones']))
        self.clave()
        self.assertEqual(self.post_json('mfa_ingreso_opciones').status_code, 429)
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.INGRESO_BLOQUEADO, actor=self.some).exists())

    def test_boton_sin_segundo_factor_no_existe_fuera_del_modo_demo(self):
        self.clave()
        pagina = self.client.get(reverse('personal_segundo_factor'))
        self.assertNotContains(pagina, 'modo demostración')
        self.assertEqual(self.client.post(reverse('personal_segundo_factor')).status_code, 404)
        self.assertFalse(self.en_sesion())

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_modo_demo_local_queda_en_la_auditoria(self):
        self.clave()
        self.client.post(reverse('personal_segundo_factor'))
        self.assertTrue(self.en_sesion())
        ingreso = RegistroAuditoria.objects.filter(accion=Accion.INGRESO, actor=self.some).latest('fecha')
        self.assertIn('SIN segundo factor', ingreso.descripcion)

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_modo_demo_no_se_ofrece_por_el_tunel(self):
        self.clave()
        respuesta = self.client.post(reverse('personal_segundo_factor'), HTTP_X_FORWARDED_FOR='1.2.3.4')
        self.assertEqual(respuesta.status_code, 404)

    # --- el Administrador quita los dispositivos (teléfono perdido) ---
    def test_administrador_quita_los_dispositivos(self):
        self.con_dispositivo()
        admin = Usuario.objects.create_user(username='admin_mfa', password=CLAVE, rut='11111111-1',
                                            tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        self.client.force_login(admin)
        self.client.post(reverse('personal_funcionario_accion', args=[self.some.pk, 'dispositivos']),
                         {'clave_admin': CLAVE, 'motivo': 'Perdió su teléfono'})
        self.assertFalse(CredencialPasskey.objects.filter(usuario=self.some).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.MFA_QUITADO, objetivo=self.some).exists())

    # --- la API no es un atajo ---
    def test_api_token_no_se_entrega_al_personal(self):
        self.some.username = 'some_api'
        self.some.save()
        respuesta = self.client.post('/api/token/', {'username': 'some_api', 'password': CLAVE})
        self.assertEqual(respuesta.status_code, 400)
        self.assertNotIn('access', respuesta.json())

    def test_api_token_cuenta_las_claves_incorrectas_del_personal(self):
        self.some.username = 'some_api'
        self.some.save()
        for _ in range(5):
            self.client.post('/api/token/', {'username': 'some_api', 'password': 'incorrecta'})
        self.some.refresh_from_db()
        self.assertIsNotNone(self.some.bloqueado_hasta)  # mismo bloqueo que la web

    def test_api_token_sigue_funcionando_para_otras_cuentas(self):
        get_user_model().objects.create_user(username='integracion', password=CLAVE)
        respuesta = self.client.post('/api/token/', {'username': 'integracion', 'password': CLAVE})
        self.assertEqual(respuesta.status_code, 200)
