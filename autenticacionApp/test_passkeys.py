"""Pruebas de enrolamiento y passkeys (B-06, RNF-SEC02, OWASP A01/A07)."""
import json
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import passkeys
from .autenticador_simulado import AutenticadorSimulado
from .models import CodigoEnrolamiento, CredencialPasskey, Usuario


DOMINIO = 'abc123-8000.brs.devtunnels.ms'


@override_settings(WEBAUTHN_RP_IDS=['localhost', DOMINIO],
                   WEBAUTHN_ORIGENES=['http://localhost:8000', f'https://{DOMINIO}'],
                   ALLOWED_HOSTS=['localhost', DOMINIO], HORASALUD_INGRESO_DEMO=False,
                   USE_X_FORWARDED_HOST=True)
class PasskeyTests(TestCase):
    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'
        call_command('cargar_datos_demo', stdout=StringIO())
        self.paciente = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PACIENTE).order_by('rut').first()
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)

    # --- utilidades ---
    def post_json(self, nombre, cuerpo='{}'):
        return self.client.post(reverse(nombre), data=cuerpo, content_type='application/json')

    def enrolar(self, autenticador):
        """Recorre el flujo completo: codigo del SOME -> RUT + codigo -> registrar passkey."""
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        return self.post_json('passkey_registro_verificar', autenticador.registrar(opciones))

    def ingresar(self, autenticador):
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        opciones = self.post_json('passkey_ingreso_opciones').json()['opciones']
        return self.post_json('passkey_ingreso_verificar', autenticador.firmar(opciones))

    # --- codigo de enrolamiento ---
    def test_codigo_se_guarda_solo_como_hash(self):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        guardado = CodigoEnrolamiento.objects.get(usuario=self.paciente)
        self.assertRegex(codigo, r'^\d{4}-\d{4}$')
        self.assertNotIn(codigo.replace('-', ''), guardado.codigo_hash)

    def test_codigo_bloqueado_tras_5_intentos(self):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        for _ in range(CodigoEnrolamiento.MAX_INTENTOS):
            with self.assertRaises(passkeys.PasskeyError):
                passkeys.validar_codigo(self.paciente, '00000000')
        with self.assertRaises(passkeys.PasskeyError):  # ni siquiera el correcto sirve ya
            passkeys.validar_codigo(self.paciente, codigo)

    def test_codigo_vencido_no_sirve(self):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        CodigoEnrolamiento.objects.update(expira_en=timezone.now() - timedelta(minutes=1))
        with self.assertRaises(passkeys.PasskeyError):
            passkeys.validar_codigo(self.paciente, codigo)

    def test_codigo_nuevo_anula_el_anterior(self):
        viejo = passkeys.generar_codigo(self.paciente, self.some)
        passkeys.generar_codigo(self.paciente, self.some)
        with self.assertRaises(passkeys.PasskeyError):
            passkeys.validar_codigo(self.paciente, viejo)

    # --- flujo real con firma criptografica ---
    def test_enrolamiento_completo_guarda_solo_clave_publica_e_inicia_sesion(self):
        respuesta = self.enrolar(AutenticadorSimulado())
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertEqual(respuesta.json()['destino'], reverse('mi_inicio'))
        credencial = CredencialPasskey.objects.get(usuario=self.paciente)
        self.assertGreater(len(bytes(credencial.clave_publica)), 60)
        self.assertIsNotNone(CodigoEnrolamiento.objects.get(usuario=self.paciente).usado_en)
        self.assertEqual(self.client.get(reverse('mi_inicio')).status_code, 200)

    def test_codigo_no_se_puede_reusar(self):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        self.post_json('passkey_registro_verificar', AutenticadorSimulado().registrar(opciones))
        self.client.post(reverse('salir'))
        respuesta = self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        self.assertContains(respuesta, 'no es válido o ya venció')

    def test_ingreso_con_passkey_real(self):
        autenticador = AutenticadorSimulado()
        self.enrolar(autenticador)
        self.client.post(reverse('salir'))
        respuesta = self.ingresar(autenticador)
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertEqual(self.client.get(reverse('mi_inicio')).status_code, 200)
        self.assertEqual(CredencialPasskey.objects.get().contador_firmas, autenticador.contador)

    def test_otra_clave_no_puede_entrar(self):
        self.enrolar(AutenticadorSimulado())
        self.client.post(reverse('salir'))
        impostor = AutenticadorSimulado()
        respuesta = self.ingresar(impostor)
        self.assertEqual(respuesta.status_code, 400)
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))

    def test_firma_alterada_se_rechaza(self):
        autenticador = AutenticadorSimulado()
        self.enrolar(autenticador)
        self.client.post(reverse('salir'))
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        opciones = self.post_json('passkey_ingreso_opciones').json()['opciones']
        otra = AutenticadorSimulado()
        otra.credencial_id = autenticador.credencial_id  # mismo id, clave distinta
        self.assertEqual(self.post_json('passkey_ingreso_verificar', otra.firmar(opciones)).status_code, 400)

    def test_sin_verificacion_de_usuario_se_rechaza(self):
        # Exige huella, rostro o PIN: no basta con tocar el dispositivo
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        respuesta = self.post_json('passkey_registro_verificar',
                                   AutenticadorSimulado(verifica_usuario=False).registrar(opciones))
        self.assertEqual(respuesta.status_code, 400)

    def test_origen_falso_se_rechaza(self):
        # Protege contra sitios de phishing que imitan a HoraSalud
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        falso = AutenticadorSimulado(origen='https://horasalud-falso.com')
        self.assertEqual(self.post_json('passkey_registro_verificar', falso.registrar(opciones)).status_code, 400)

    def test_reto_sirve_una_sola_vez(self):
        autenticador = AutenticadorSimulado()
        self.enrolar(autenticador)
        self.client.post(reverse('salir'))
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        opciones = self.post_json('passkey_ingreso_opciones').json()['opciones']
        firmado = autenticador.firmar(opciones)
        self.post_json('passkey_ingreso_verificar', firmado)
        self.client.post(reverse('salir'))
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertEqual(self.post_json('passkey_ingreso_verificar', firmado).status_code, 400)  # repeticion

    # --- pantallas y permisos ---
    def test_sin_modo_demo_no_se_entra_sin_huella(self):
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertContains(self.client.get(reverse('verificar')), 'Tengo un código del SOME')
        self.assertEqual(self.client.post(reverse('verificar')).status_code, 404)

    def test_some_debe_confirmar_la_cedula(self):
        self.client.force_login(self.some)
        respuesta = self.client.post(reverse('some_enrolar'), {'rut': self.paciente.rut}, follow=True)
        self.assertContains(respuesta, 'Confirma que revisaste la cédula')
        self.assertFalse(CodigoEnrolamiento.objects.exists())
        respuesta = self.client.post(reverse('some_enrolar'), {'rut': self.paciente.rut, 'cedula_validada': 'si'})
        self.assertContains(respuesta, 'Vence en 30 minutos')
        self.assertTrue(CodigoEnrolamiento.objects.filter(usuario=self.paciente, creado_por=self.some).exists())

    def test_paciente_no_genera_codigos(self):
        self.client.force_login(self.paciente)
        self.assertRedirects(self.client.get(reverse('some_enrolar')), reverse('inicio'))


    # --- B-16: dominio HTTPS del tunel (telefono) ---
    def usar_dominio_publico(self):
        self.client.defaults.update(HTTP_HOST=DOMINIO, HTTP_X_FORWARDED_PROTO='https')

    def test_telefono_enrola_e_ingresa_por_el_dominio_publico(self):
        self.usar_dominio_publico()
        telefono = AutenticadorSimulado(rp_id=DOMINIO, origen=f'https://{DOMINIO}')
        self.assertEqual(self.enrolar(telefono).status_code, 200)
        self.assertEqual(CredencialPasskey.objects.get().rp_id, DOMINIO)
        self.client.post(reverse('salir'))
        self.assertEqual(self.ingresar(telefono).status_code, 200)

    def test_passkey_del_notebook_no_sirve_en_el_dominio_publico(self):
        self.enrolar(AutenticadorSimulado())  # creada en localhost
        self.client.post(reverse('salir'))
        self.usar_dominio_publico()
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertContains(self.client.get(reverse('verificar')), 'Tengo un código del SOME')
        self.assertEqual(self.post_json('passkey_ingreso_opciones').status_code, 403)

    def test_firma_hecha_para_otro_dominio_se_rechaza(self):
        self.usar_dominio_publico()
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})
        opciones = self.post_json('passkey_registro_opciones').json()['opciones']
        falso = AutenticadorSimulado(rp_id='localhost', origen=f'https://{DOMINIO}')
        self.assertEqual(self.post_json('passkey_registro_verificar', falso.registrar(opciones)).status_code, 400)

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_modo_demo_bloqueado_desde_internet(self):
        self.usar_dominio_publico()
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertNotContains(self.client.get(reverse('verificar')), 'modo demostración')
        self.assertEqual(self.client.post(reverse('verificar')).status_code, 404)

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_tunel_que_reescribe_host_usa_el_dominio_publico(self):
        # Dev Tunnels puede entregar Host=localhost y el dominio real en X-Forwarded-Host
        self.client.defaults.update(HTTP_HOST='localhost:8000', HTTP_X_FORWARDED_HOST=DOMINIO,
                                    HTTP_X_FORWARDED_PROTO='https')
        telefono = AutenticadorSimulado(rp_id=DOMINIO, origen=f'https://{DOMINIO}')
        self.assertEqual(self.enrolar(telefono).status_code, 200)
        self.assertEqual(CredencialPasskey.objects.get().rp_id, DOMINIO)

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_modo_demo_sigue_en_el_notebook(self):
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertRedirects(self.client.post(reverse('verificar')), reverse('mi_inicio'))

    @override_settings(HORASALUD_INGRESO_DEMO=True)
    def test_no_se_puede_falsificar_localhost_desde_el_tunel(self):
        self.client.defaults.update(HTTP_X_FORWARDED_HOST='localhost', HTTP_X_FORWARDED_FOR='203.0.113.9')
        self.client.post(reverse('ingresar'), {'rut': self.paciente.rut})
        self.assertEqual(self.client.post(reverse('verificar')).status_code, 404)

    @override_settings(CSRF_TRUSTED_ORIGINS=[f'https://{DOMINIO}', 'http://localhost:8000'],
                       SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_formulario_por_tunel_que_reescribe_origin(self):
        # Defecto DEF-02 (B-16): el tunel cambia Origin a localhost y Django devolvia 403 CSRF
        cliente = Client(enforce_csrf_checks=True, HTTP_HOST='localhost:8000', HTTP_X_FORWARDED_HOST=DOMINIO,
                         HTTP_X_FORWARDED_PROTO='https', HTTP_ORIGIN='http://localhost:8000')
        token = cliente.get(reverse('ingresar')).cookies['csrftoken'].value
        respuesta = cliente.post(reverse('ingresar'), {'rut': self.paciente.rut, 'csrfmiddlewaretoken': token})
        self.assertRedirects(respuesta, reverse('verificar'), fetch_redirect_response=False)
        # Sin token CSRF se sigue rechazando
        self.assertEqual(cliente.post(reverse('ingresar'), {'rut': self.paciente.rut}).status_code, 403)
