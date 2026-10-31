"""Pruebas de B-07: consentimiento, derechos ARCO+ y cifrado en reposo (Ley 21.719, RNF-SEC02)."""
import json
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from agendaApp.models import Hora
from proyectoHoraSalud.cifrado import PREFIJO

from . import passkeys
from .models import Consentimiento, CredencialPasskey, Paciente, SolicitudDerechos, Usuario


@override_settings(HORASALUD_INGRESO_DEMO=False)
class ConsentimientoTests(TestCase):
    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.paciente = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PACIENTE).order_by('rut').first()
        # Persona recién inscrita: todavía no ha aceptado la política
        self.paciente.consentimientos.all().delete()

    def iniciar_enrolamiento(self):
        codigo = passkeys.generar_codigo(self.paciente, self.some)
        return self.client.post(reverse('enrolar'), {'rut': self.paciente.rut, 'codigo': codigo})

    def test_enrolamiento_pide_la_politica_antes_de_la_huella(self):
        self.assertRedirects(self.iniciar_enrolamiento(), reverse('enrolar_consentimiento'))
        self.assertRedirects(self.client.get(reverse('enrolar_huella')), reverse('enrolar_consentimiento'))
        self.assertEqual(self.client.post(reverse('passkey_registro_opciones')).status_code, 403)

    def test_acepta_y_queda_registrada_la_version(self):
        self.iniciar_enrolamiento()
        respuesta = self.client.post(reverse('enrolar_consentimiento'), {'decision': 'acepto'})
        self.assertRedirects(respuesta, reverse('enrolar_huella'))
        consentimiento = Consentimiento.objects.get(usuario=self.paciente)
        self.assertTrue(consentimiento.aceptado)
        self.assertEqual(consentimiento.version, '1.0')
        self.assertEqual(self.client.post(reverse('passkey_registro_opciones')).status_code, 200)

    def test_no_acepta_no_se_activa_la_huella(self):
        self.iniciar_enrolamiento()
        respuesta = self.client.post(reverse('enrolar_consentimiento'), {'decision': 'rechazo'})
        self.assertContains(respuesta, 'respetamos tu decisión')
        self.assertFalse(Consentimiento.objects.get(usuario=self.paciente).aceptado)
        self.assertEqual(self.client.post(reverse('passkey_registro_opciones')).status_code, 403)

    def test_sesion_sin_consentimiento_pide_aceptar(self):
        self.client.force_login(self.paciente)
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('aceptar_politica'))
        self.client.post(reverse('aceptar_politica'), {'decision': 'acepto'})
        self.assertEqual(self.client.get(reverse('mi_inicio')).status_code, 200)

    def test_rechazar_al_ingresar_cierra_la_sesion(self):
        self.client.force_login(self.paciente)
        self.client.post(reverse('aceptar_politica'), {'decision': 'rechazo'})
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))

    def test_nueva_version_de_la_politica_se_vuelve_a_pedir(self):
        Consentimiento.objects.create(usuario=self.paciente, version='1.0', aceptado=True)
        self.client.force_login(self.paciente)
        self.assertEqual(self.client.get(reverse('mi_inicio')).status_code, 200)
        with mock.patch('autenticacionApp.privacidad.VERSION_POLITICA', '2.0'):
            self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('aceptar_politica'))

    def test_politica_es_publica(self):
        self.assertContains(self.client.get(reverse('politica')), 'Lo que NO guardamos')


class MisDatosTests(TestCase):
    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.paciente = Paciente.objects.filter(horas__isnull=False).select_related('usuario').first().usuario
        self.otro = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PACIENTE).exclude(pk=self.paciente.pk).first()
        self.client.force_login(self.paciente)

    def test_mis_datos_muestra_datos_y_dispositivos(self):
        CredencialPasskey.objects.create(usuario=self.paciente, credencial_id='abc', clave_publica=b'x',
                                         dispositivo='Chrome en Android')
        respuesta = self.client.get(reverse('mis_datos'))
        self.assertContains(respuesta, self.paciente.rut)
        self.assertContains(respuesta, 'Chrome en Android')

    def test_descarga_de_datos_portabilidad(self):
        CredencialPasskey.objects.create(usuario=self.paciente, credencial_id='abc', clave_publica=b'secreta')
        respuesta = self.client.get(reverse('descargar_mis_datos'))
        self.assertIn('attachment', respuesta['Content-Disposition'])
        datos = json.loads(respuesta.content)
        self.assertEqual(datos['persona']['rut'], self.paciente.rut)
        self.assertTrue(datos['paciente']['horas'])
        self.assertNotIn('clave_publica', respuesta.content.decode())

    def test_no_puede_borrar_dispositivos_ajenos(self):
        ajena = CredencialPasskey.objects.create(usuario=self.otro, credencial_id='ajena', clave_publica=b'x')
        self.assertEqual(self.client.post(reverse('borrar_dispositivo', args=[ajena.pk])).status_code, 404)
        self.assertTrue(CredencialPasskey.objects.filter(pk=ajena.pk).exists())

    def test_borra_su_propio_dispositivo(self):
        propia = CredencialPasskey.objects.create(usuario=self.paciente, credencial_id='propia', clave_publica=b'x')
        self.client.post(reverse('borrar_dispositivo', args=[propia.pk]))
        self.assertFalse(CredencialPasskey.objects.filter(pk=propia.pk).exists())

    def test_solicitud_arco_y_el_some_la_resuelve(self):
        self.client.post(reverse('solicitar_derecho'), {'tipo': 'rectificacion', 'detalle': 'Mi teléfono cambió'})
        solicitud = SolicitudDerechos.objects.get(usuario=self.paciente)
        self.assertEqual(solicitud.detalle, 'Mi teléfono cambió')
        # Un paciente no entra al panel de solicitudes
        self.assertRedirects(self.client.get(reverse('some_solicitudes')), reverse('inicio'))
        self.client.force_login(Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO))
        self.client.post(reverse('some_solicitudes'), {'solicitud': solicitud.pk, 'respuesta': 'Corregido'})
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudDerechos.Estado.RESUELTA)

    def test_retirar_consentimiento(self):
        CredencialPasskey.objects.create(usuario=self.paciente, credencial_id='propia', clave_publica=b'x')
        respuesta = self.client.post(reverse('retirar_consentimiento'))
        self.assertContains(respuesta, 'Retiraste tu consentimiento')
        self.assertFalse(self.paciente.passkeys.exists())
        self.assertIsNotNone(self.paciente.consentimientos.first().retirado_en)
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('ingresar'))  # sesión cerrada


class CifradoTests(TestCase):
    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())

    def valor_en_bd(self, objeto, campo):
        # Lee la columna tal como quedó en la base, sin pasar por el modelo
        tabla = connection.ops.quote_name(objeto._meta.db_table)
        columna = connection.ops.quote_name(objeto._meta.get_field(campo).column)
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT {columna} FROM {tabla} WHERE id = %s', [objeto.pk.hex])
            return cursor.fetchone()[0]

    def test_telefono_se_guarda_cifrado(self):
        usuario = Usuario.objects.exclude(telefono='').first()
        crudo = self.valor_en_bd(usuario, 'telefono')
        self.assertTrue(crudo.startswith(PREFIJO))
        self.assertNotIn(usuario.telefono.replace('+', ''), crudo)
        self.assertTrue(usuario.telefono.startswith('+569'))  # la app lo lee descifrado

    def test_motivo_de_cancelacion_se_guarda_cifrado(self):
        hora = Hora.objects.exclude(motivo_cancelacion='').first()
        crudo = self.valor_en_bd(hora, 'motivo_cancelacion')
        self.assertTrue(crudo.startswith(PREFIJO))
        self.assertNotIn('avisa', crudo)
        self.assertIn('avisa', hora.motivo_cancelacion)
