"""DEF-10 (CP-31): mitigación de las dos denegaciones de servicio de DRF 3.17 que aplican a la API."""
from django.test import TestCase, override_settings


@override_settings(ALLOWED_HOSTS=['testserver'])
class CabecerasSegurasApiTests(TestCase):
    def test_api_normal_sigue_funcionando(self):
        respuesta = self.client.get('/api/salud/', HTTP_ACCEPT='application/json')
        self.assertEqual(respuesta.status_code, 200)

    def test_accept_enorme_se_rechaza(self):
        respuesta = self.client.get('/api/salud/', HTTP_ACCEPT='application/json;q=0.9,' * 200)
        self.assertEqual(respuesta.status_code, 400)

    def test_charset_de_compresion_se_rechaza(self):
        for charset in ('zlib_codec', 'bz2', '"zlib"'):
            # generic() envía los bytes tal cual (post() intentaría codificarlos con ese charset)
            respuesta = self.client.generic('POST', '/api/token/', b'x', content_type=f'application/json; charset={charset}')
            self.assertEqual(respuesta.status_code, 400, charset)

    def test_utf8_se_acepta(self):
        respuesta = self.client.post('/api/token/', data=b'{}', content_type='application/json; charset=UTF-8')
        self.assertNotEqual(respuesta.status_code, 500)
        self.assertNotIn(b'UTF-8.', respuesta.content)

    def test_paginas_fuera_de_la_api_no_se_tocan(self):
        respuesta = self.client.get('/', HTTP_ACCEPT='text/html,' * 200)
        self.assertEqual(respuesta.status_code, 200)
