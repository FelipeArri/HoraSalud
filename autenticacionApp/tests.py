from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .adapter_inscripcion import AdapterFonasa, AdapterSistemaClinico
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


class AdapterTests(APITestCase):
    """Patron Adapter (D26-C03): traducen el formato de cada sistema externo al de HoraSalud."""

    def test_sistema_clinico_inscrito(self):
        ficha = {'nombres': 'Ana', 'apellido_paterno': 'Prueba', 'apellido_materno': 'Ficticia',
                 'sector': 'SECTOR 2', 'estado_inscripcion': 'ACTIVA', 'fono': '+569'}
        datos = AdapterSistemaClinico(ClienteFalso(ficha)).consultar_inscripcion('11111111-1')
        self.assertEqual((datos['inscrito'], datos['apellidos'], datos['sector']), (True, 'Prueba Ficticia', 'Sector 2'))

    def test_sistema_clinico_sin_registro_o_pasivo(self):
        self.assertFalse(AdapterSistemaClinico(ClienteFalso(None)).consultar_inscripcion('1-9')['inscrito'])
        pasivo = {'estado_inscripcion': 'PASIVA'}
        self.assertFalse(AdapterSistemaClinico(ClienteFalso(pasivo)).consultar_inscripcion('1-9')['inscrito'])

    def test_fonasa_tramo_e_isapre(self):
        fonasa = AdapterFonasa(ClienteFalso({'codigo_prevision': 'FONASA', 'tramo': 'B', 'afiliado_vigente': True}))
        self.assertEqual(fonasa.consultar_prevision('1-9'), {'prevision': 'fonasa', 'tramo': 'B', 'vigente': True})
        isapre = AdapterFonasa(ClienteFalso({'codigo_prevision': 'ISAPRE', 'afiliado_vigente': True}))
        self.assertEqual(isapre.consultar_prevision('1-9')['prevision'], 'isapre')
        sin = AdapterFonasa(ClienteFalso(None))
        self.assertEqual(sin.consultar_prevision('1-9')['prevision'], 'sin_prevision')
