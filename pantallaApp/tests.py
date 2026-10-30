from django.test import TestCase
from django.urls import reverse


class InicioTests(TestCase):
    def test_pagina_de_inicio_responde(self):
        respuesta = self.client.get(reverse('inicio'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'HoraSalud')

    def test_cabeceras_de_seguridad(self):
        # OWASP A05 y RNF-SEC02
        respuesta = self.client.get(reverse('inicio'))
        self.assertEqual(respuesta['X-Frame-Options'], 'DENY')
        self.assertEqual(respuesta['X-Content-Type-Options'], 'nosniff')
