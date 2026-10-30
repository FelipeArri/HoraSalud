from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .adapter_inscripcion import AdapterInscripcionFonasa
from .validators import calcular_dv, validar_rut

User = get_user_model()


class ValidarRutTests(SimpleTestCase):
    def test_rut_valido(self):
        # RF-01 escenario positivo
        validar_rut('11.111.111-1')
        validar_rut('12345678-5')

    def test_digito_verificador_incorrecto(self):
        # RF-01 escenario negativo
        with self.assertRaises(ValidationError):
            validar_rut('12345678-9')

    def test_formato_invalido_o_inyeccion(self):
        # RF-01 y OWASP A03: entrada maliciosa en el RUT
        for entrada in ['abc', '1234-5', "1' OR '1'='1", '<script>']:
            with self.assertRaises(ValidationError):
                validar_rut(entrada)

    def test_digito_k(self):
        self.assertEqual(calcular_dv('10000013'), 'K')


class SaludApiTests(APITestCase):
    def test_salud_responde_sin_token(self):
        respuesta = self.client.get('/api/salud/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data, {'api': 'ok', 'baseDatos': 'ok'})


class JwtTests(APITestCase):
    def setUp(self):
        User.objects.create_user(username='prueba', password='Clave-de-prueba-123')

    def test_token_con_credenciales_validas(self):
        respuesta = self.client.post('/api/token/', {'username': 'prueba', 'password': 'Clave-de-prueba-123'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)

    def test_token_con_clave_incorrecta_responde_401(self):
        # OWASP A07
        respuesta = self.client.post('/api/token/', {'username': 'prueba', 'password': 'incorrecta'})
        self.assertEqual(respuesta.status_code, 401)

    def test_token_alterado_responde_401(self):
        # OWASP A07: un token modificado no se acepta
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token.alterado.invalido')
        respuesta = self.client.post('/api/token/refresh/', {'refresh': 'token.alterado.invalido'})
        self.assertEqual(respuesta.status_code, 401)


class ClienteFalso:
    def __init__(self, respuesta):
        self.respuesta = respuesta

    def obtener(self, ruta):
        return self.respuesta


class AdapterInscripcionTests(APITestCase):
    def test_rut_inscrito_asigna_sector(self):
        # RF-01 escenario positivo (datos ficticios)
        adapter = AdapterInscripcionFonasa(ClienteFalso({'vigente': True, 'comuna': 'La Granja - Sector 2'}))
        self.assertEqual(adapter.consultar_inscripcion('11111111-1'), {'vigente': True, 'sector': 2})

    def test_rut_no_inscrito(self):
        # RF-01 escenario negativo
        adapter = AdapterInscripcionFonasa(ClienteFalso(None))
        self.assertEqual(adapter.consultar_inscripcion('22222222-2'), {'vigente': False, 'sector': None})
