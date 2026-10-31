"""Pruebas del ingreso (RF-01, RF-03, RN-07)."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Paciente, Usuario


@override_settings(HORASALUD_INGRESO_DEMO=True)
class IngresoTests(TestCase):
    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'  # el modo demo solo existe en el notebook
        call_command('cargar_datos_demo', stdout=StringIO())
        self.paciente = Paciente.objects.filter(tutor__isnull=True).select_related('usuario').first()

    def test_rut_con_digito_incorrecto_se_rechaza(self):
        cuerpo, dv = self.paciente.usuario.rut.split('-')
        malo = '0' if dv != '0' else '1'
        respuesta = self.client.post(reverse('ingresar'), {'rut': f'{cuerpo}-{malo}'})
        self.assertContains(respuesta, 'dígito verificador')

    def test_rut_no_inscrito_no_revela_datos(self):
        respuesta = self.client.post(reverse('ingresar'), {'rut': '11.111.111-1'})
        self.assertContains(respuesta, 'No encontramos una inscripción activa')

    def test_rut_con_puntos_lleva_a_verificar_y_luego_al_inicio(self):
        cuerpo, dv = self.paciente.usuario.rut.split('-')
        con_puntos = f'{int(cuerpo):,}'.replace(',', '.') + f'-{dv}'
        respuesta = self.client.post(reverse('ingresar'), {'rut': con_puntos})
        self.assertRedirects(respuesta, reverse('verificar'))
        respuesta = self.client.post(reverse('verificar'))
        self.assertRedirects(respuesta, reverse('mi_inicio'))
        self.assertContains(self.client.get(reverse('mi_inicio')), self.paciente.usuario.first_name)

    @override_settings(HORASALUD_INGRESO_DEMO=False)
    def test_sin_modo_demo_no_se_entra_solo_con_rut(self):
        self.client.post(reverse('ingresar'), {'rut': self.paciente.usuario.rut})
        self.assertEqual(self.client.post(reverse('verificar')).status_code, 404)  # B-06: solo con passkey

    def test_tutor_elige_solo_a_sus_dependientes(self):
        # RF-03 y RN-07
        tutor = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.TUTOR).first()
        propio = Paciente.objects.get(tutor=tutor)
        ajeno = Paciente.objects.exclude(tutor=tutor).first()
        self.client.force_login(tutor)
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('elegir_paciente'))
        self.client.post(reverse('elegir_paciente'), {'paciente': ajeno.pk})
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('elegir_paciente'))
        self.client.post(reverse('elegir_paciente'), {'paciente': propio.pk})
        self.assertContains(self.client.get(reverse('mi_inicio')), propio.usuario.get_full_name())

    def test_paginas_privadas_piden_ingreso(self):
        # RN-12: sin sesion no se ve informacion de agendamiento
        for nombre in ['mi_inicio', 'mis_horas', 'pedir_especialidad', 'some_nomina']:
            self.assertRedirects(self.client.get(reverse(nombre)), reverse('ingresar'))

    def test_paciente_no_entra_al_some(self):
        self.client.force_login(self.paciente.usuario)
        self.assertRedirects(self.client.get(reverse('some_nomina')), reverse('inicio'))

    def test_salir_cierra_la_sesion(self):
        self.client.force_login(self.paciente.usuario)
        self.client.post(reverse('salir'))
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))

    def test_def03_paginas_privadas_no_quedan_en_cache(self):
        # DEF-03: al ir "atras" tras cerrar sesion no deben verse datos del paciente
        self.client.force_login(self.paciente.usuario)
        respuesta = self.client.get(reverse('mi_inicio'))
        self.assertIn('no-store', respuesta['Cache-Control'])
        salida = self.client.post(reverse('salir'))
        self.assertEqual(salida['Clear-Site-Data'], '"cache"')
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))

    def test_portada_publica_si_se_puede_guardar(self):
        self.assertNotIn('no-store', self.client.get(reverse('inicio')).get('Cache-Control', ''))
