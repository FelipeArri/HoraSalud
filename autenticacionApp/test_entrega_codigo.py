"""Pruebas de B-18: entrega de código validada con el sistema clínico y FONASA (RF-01, RN-15)."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from . import inscripcion, passkeys
from .models import CodigoEnrolamiento, Paciente, Usuario

NUEVA_FONASA = '31000001-9'
ISAPRE, DIPRECA, CAPREDENA = '31000002-7', '31000003-5', '31000004-3'
SIN_PREVISION, NO_INSCRITO, PASIVO = '31000005-1', '31000006-K', '31000007-8'


class ConsultaTests(TestCase):
    databases = {'default', 'fonasa'}  # tambien consulta el padron FONASA simulado

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())

    def test_paciente_demo_inscrito_con_fonasa(self):
        consulta = inscripcion.consultar('30000007-K')
        self.assertTrue(consulta.puede_recibir_codigo)
        self.assertEqual(consulta.inscripcion['sector'], 'Sector 1')
        self.assertEqual(consulta.tramo_texto, 'FONASA tramo A')

    def test_rechazos(self):
        for rut, texto in [(ISAPRE, 'ISAPRE'), (DIPRECA, 'DIPRECA'), (CAPREDENA, 'CAPREDENA'),
                           (SIN_PREVISION, 'carente de recursos'), (NO_INSCRITO, 'Debe inscribirse'),
                           (PASIVO, 'Debe inscribirse')]:
            consulta = inscripcion.consultar(rut)
            self.assertFalse(consulta.puede_recibir_codigo, rut)
            self.assertIn(texto, consulta.motivo_rechazo)

    def test_tutor_no_requiere_inscripcion_ni_fonasa(self):
        tutor = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.TUTOR).first()
        consulta = inscripcion.consultar(tutor.rut)
        self.assertTrue(consulta.es_tutor and consulta.puede_recibir_codigo)


class PantallaSomeTests(TestCase):
    databases = {'default', 'fonasa'}  # tambien consulta el padron FONASA simulado

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(self.some)

    def generar(self, rut, **extra):
        return self.client.post(reverse('some_enrolar'), {'rut': rut, 'cedula_validada': 'si', **extra})

    def test_persona_nueva_se_registra_con_datos_oficiales(self):
        self.assertContains(self.client.get(reverse('some_enrolar'), {'rut': NUEVA_FONASA}), 'FONASA tramo B')
        respuesta = self.generar(NUEVA_FONASA)
        self.assertContains(respuesta, 'Vence en 30 minutos')
        usuario = Usuario.objects.get(rut=NUEVA_FONASA)
        paciente = Paciente.objects.get(usuario=usuario)
        self.assertEqual(usuario.get_full_name(), 'Ana María Prueba Ficticia')
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual((paciente.sector.nombre, paciente.tramo), ('Sector 2', 'B'))
        self.assertIsNotNone(paciente.prevision_consultada_en)
        self.assertEqual(CodigoEnrolamiento.objects.get(usuario=usuario).creado_por, self.some)

    def test_isapre_no_recibe_codigo_ni_se_registra(self):
        respuesta = self.generar(ISAPRE)
        self.assertContains(respuesta, 'no pertenece al consultorio')
        self.assertFalse(Usuario.objects.filter(rut=ISAPRE).exists())
        self.assertFalse(CodigoEnrolamiento.objects.exists())

    def test_no_inscrito_no_recibe_codigo(self):
        self.assertContains(self.client.get(reverse('some_enrolar'), {'rut': NO_INSCRITO}), 'no inscrito en el CESFAM')
        self.generar(NO_INSCRITO)
        self.assertFalse(CodigoEnrolamiento.objects.exists())

    def test_sin_cedula_no_hay_codigo(self):
        self.client.post(reverse('some_enrolar'), {'rut': NUEVA_FONASA})
        self.assertFalse(CodigoEnrolamiento.objects.exists())

    def test_codigo_vigente_avisa_y_pide_confirmar_reemplazo(self):
        paciente = Usuario.objects.get(rut='30000007-K')
        passkeys.generar_codigo(paciente, self.some)
        self.assertContains(self.client.get(reverse('some_enrolar'), {'rut': '30000007-K'}), 'código vigente')
        self.assertContains(self.generar('30000007-K'), 'Confirma que quieres reemplazarlo', status_code=200)
        self.assertEqual(CodigoEnrolamiento.objects.filter(usuario=paciente).count(), 1)
        self.assertContains(self.generar('30000007-K', reemplazar='si'), 'Vence en 30 minutos')
        self.assertEqual(CodigoEnrolamiento.objects.filter(usuario=paciente).count(), 2)

    def test_la_persona_nueva_completa_el_enrolamiento(self):
        # Integración: SOME genera el código → la persona lo usa → acepta la política
        self.generar(NUEVA_FONASA)
        usuario = Usuario.objects.get(rut=NUEVA_FONASA)
        codigo = passkeys.generar_codigo(usuario, self.some)
        self.client.logout()
        respuesta = self.client.post(reverse('enrolar'), {'rut': NUEVA_FONASA, 'codigo': codigo})
        self.assertRedirects(respuesta, reverse('enrolar_consentimiento'))
        self.assertRedirects(self.client.post(reverse('enrolar_consentimiento'), {'decision': 'acepto'}),
                             reverse('enrolar_huella'))
