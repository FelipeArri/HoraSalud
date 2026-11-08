"""
Trazabilidad (RN-11): cada registro de auditoría dice quién actuó (con su rol),
qué hizo y sobre quién. Incluye ingresos y salidas de todos los roles.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .auditoria_texto import armar_descripcion
from .models import Paciente, RegistroAuditoria, Usuario

ACCION = RegistroAuditoria.Accion
CLAVE = 'Prueba-Auditoria-2026'


class ArmarDescripcionTests(TestCase):
    def test_frase_completa(self):
        texto = armar_descripcion('Reservó una hora', 'Administrativo SOME', 'María Soto', '11111111-1',
                                  'Paciente', 'Raúl Carrasco', '30000016-9', 'Medicina General')
        self.assertEqual(texto, 'Administrativo SOME María Soto (11111111-1): Reservó una hora · sobre '
                                'Paciente Raúl Carrasco (30000016-9). Medicina General')

    def test_sin_actor_es_el_sistema(self):
        self.assertTrue(armar_descripcion('Canceló una hora').startswith('Sistema HoraSalud: '))

    def test_no_repite_a_la_persona_cuando_actua_sobre_si_misma(self):
        texto = armar_descripcion('Ingreso al sistema', 'Paciente', 'Ana', '1-9', 'Paciente', 'Ana', '1-9')
        self.assertNotIn('sobre', texto)


@override_settings(HORASALUD_INGRESO_DEMO=True)
class IngresoQuedaRegistradoTests(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def ultimo(self, accion):
        return RegistroAuditoria.objects.filter(accion=accion).first()

    def test_ingreso_y_salida_de_paciente_con_rol_y_metodo(self):
        paciente = Paciente.objects.select_related('usuario').first().usuario
        self.client.post(reverse('ingresar'), {'rut': paciente.rut})
        self.client.post(reverse('verificar'))
        registro = self.ultimo(ACCION.INGRESO)
        self.assertEqual((registro.actor, registro.actor_rol), (paciente, 'Paciente'))
        self.assertIn(f'Paciente {paciente.get_full_name()} ({paciente.rut})', registro.descripcion)
        self.assertIn('modo demostración', registro.descripcion)

        self.client.post(reverse('salir'))
        salida = self.ultimo(ACCION.SALIDA)
        self.assertEqual(salida.actor, paciente)
        self.assertIn('Cerró sesión', salida.descripcion)

    def test_ingreso_del_personal_dice_su_rol(self):
        some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        some.set_password(CLAVE)
        some.save()
        self.client.post(reverse('personal_ingresar'), {'rut': some.rut, 'clave': CLAVE})
        registro = self.ultimo(ACCION.INGRESO)
        self.assertEqual(registro.actor_rol, 'Administrativo SOME')
        self.assertIn('Entró con RUT y clave', registro.descripcion)
        self.assertEqual(RegistroAuditoria.objects.filter(accion=ACCION.INGRESO).count(), 1)  # sin duplicados

    def test_tutor_deja_registro_de_por_quien_actua(self):
        dependiente = Paciente.objects.filter(tutor__isnull=False).select_related('usuario', 'tutor').first()
        self.client.force_login(dependiente.tutor)
        self.client.post(reverse('elegir_paciente'), {'paciente': dependiente.pk})
        registro = self.ultimo(ACCION.TUTOR_ACTUA)
        self.assertEqual((registro.actor_rol, registro.objetivo_rol), ('Tutor', 'Paciente'))
        self.assertIn(f'sobre Paciente {dependiente.usuario.get_full_name()}', registro.descripcion)

    def test_pantalla_de_actividad_muestra_rol_en_pestana_de_pacientes(self):
        admin = Usuario.objects.create(username='admin_prueba', rut='32000001-7', first_name='Marcela',
                                       tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        paciente = Paciente.objects.select_related('usuario').first().usuario
        self.client.force_login(paciente)
        self.client.post(reverse('salir'))
        self.client.force_login(admin)
        pantalla = self.client.get(reverse('personal_auditoria'), {'ver': 'horas'})
        self.assertContains(pantalla, 'Cerró sesión')
        self.assertContains(pantalla, f'Paciente · {paciente.rut}')
        self.assertNotContains(self.client.get(reverse('personal_auditoria')), f'Paciente · {paciente.rut}')


class FaviconTests(TestCase):
    def test_paginas_enlazan_el_favicon(self):
        self.assertContains(self.client.get(reverse('inicio')), 'images/favicon.svg')

    def test_ruta_por_defecto_del_navegador(self):
        respuesta = self.client.get('/favicon.ico')
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta['Location'].endswith('images/favicon.ico'))
