"""Pruebas de B-20: ingreso del personal, Administrador CESFAM, reautenticación y auditoría."""
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from agendaApp.models import Especialidad

from .models import Profesional, RegistroAuditoria, Usuario

Accion = RegistroAuditoria.Accion


class PersonalBase(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.carpeta = Path(tempfile.mkdtemp())
        with override_settings(REPORTES_DIR=self.carpeta):
            call_command('cargar_funcionarios', stdout=StringIO())
        hoja = load_workbook(self.carpeta / 'cuentas_personal.xlsx').active
        self.claves = {hoja.cell(f, 1).value: hoja.cell(f, 2).value for f in range(6, hoja.max_row + 1)}
        self.admin = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        self.some = Usuario.objects.get(username__startswith='demo_', tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)

    def ingresar(self, usuario, clave=None):
        return self.client.post(reverse('personal_ingresar'),
                                {'rut': usuario.rut, 'clave': clave or self.claves[usuario.rut]})


class PrecargaTests(PersonalBase):
    def test_excel_con_el_personal_precargado(self):
        # Administrador + 2 SOME + 3 profesionales demo
        self.assertEqual(len(self.claves), 6)
        self.assertIn(self.admin.rut, self.claves)
        for rut, clave in self.claves.items():
            self.assertTrue(Usuario.objects.get(rut=rut).check_password(clave))
        self.assertFalse(Usuario.objects.filter(rut__in=self.claves, password__in=self.claves.values()).exists())


class IngresoTests(PersonalBase):
    def test_cada_cargo_llega_a_su_pantalla(self):
        profesional = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PROFESIONAL).first()
        for usuario, destino in [(self.admin, 'personal_funcionarios'), (self.some, 'some_nomina'),
                                 (profesional, 'profesional_agenda')]:
            self.assertRedirects(self.ingresar(usuario), reverse(destino), fetch_redirect_response=False)
            self.assertEqual(self.client.get(reverse(destino)).status_code, 200)
            self.client.logout()
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.INGRESO, actor=self.admin).exists())

    def test_clave_incorrecta_mensaje_generico_y_bloqueo_a_los_5(self):
        for _ in range(4):
            r = self.ingresar(self.some, 'incorrecta')
            self.assertContains(r, 'RUT o clave incorrectos')
        r = self.ingresar(self.some, 'incorrecta')
        self.some.refresh_from_db()
        self.assertIsNotNone(self.some.bloqueado_hasta)
        # Bloqueada: ni con la clave correcta entra
        self.assertContains(self.ingresar(self.some), 'Cuenta bloqueada')
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.CUENTA_BLOQUEADA).exists())

    def test_paciente_no_entra_por_ingreso_de_personal(self):
        paciente = Usuario.objects.filter(tipo_usuario=Usuario.Tipo.PACIENTE).first()
        paciente.set_password('ClaveDePrueba123')
        paciente.save()
        self.assertContains(self.ingresar(paciente, 'ClaveDePrueba123'), 'RUT o clave incorrectos')

    def test_solo_el_administrador_ve_funcionarios(self):
        self.ingresar(self.some)
        self.assertRedirects(self.client.get(reverse('personal_funcionarios')), reverse('inicio'),
                             fetch_redirect_response=False)


class AdministradorTests(PersonalBase):
    def setUp(self):
        super().setUp()
        self.ingresar(self.admin)
        self.clave_admin = self.claves[self.admin.rut]
        self.especialidad = Especialidad.objects.first()

    def datos_nuevo(self, **extra):
        datos = {'rut': '32000020-3', 'nombres': 'Nora', 'apellidos': 'Fuentes Gil', 'tipo': 'profesional',
                 'especialidad': self.especialidad.pk, 'box': 'B-09', 'email': '', 'clave_admin': self.clave_admin}
        datos.update(extra)
        return datos

    def test_agregar_funcionario_con_clave_temporal(self):
        r = self.client.post(reverse('personal_funcionario_nuevo'), self.datos_nuevo())
        self.assertContains(r, 'Se muestra solo esta vez')
        nueva = Usuario.objects.get(rut='32000020-3')
        clave = r.context['clave']
        self.assertTrue(nueva.check_password(clave) and nueva.debe_cambiar_clave)
        self.assertEqual(Profesional.objects.get(usuario=nueva).box_atencion, 'B-09')
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.ALTA, actor=self.admin, objetivo=nueva).exists())
        # Primer ingreso: obliga a cambiar la clave antes de ver su agenda
        self.client.logout()
        self.assertRedirects(self.ingresar(nueva, clave), reverse('personal_cambiar_clave'),
                             fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('profesional_agenda')), reverse('personal_cambiar_clave'),
                             fetch_redirect_response=False)
        self.client.post(reverse('personal_cambiar_clave'), {
            'old_password': clave, 'new_password1': 'Consultorio#2026', 'new_password2': 'Consultorio#2026'})
        nueva.refresh_from_db()
        self.assertFalse(nueva.debe_cambiar_clave)
        self.assertEqual(self.client.get(reverse('profesional_agenda')).status_code, 200)

    def test_profesional_sin_especialidad_no_se_crea(self):
        r = self.client.post(reverse('personal_funcionario_nuevo'), self.datos_nuevo(especialidad=''))
        self.assertContains(r, 'Elige la especialidad')
        self.assertFalse(Usuario.objects.filter(rut='32000020-3').exists())

    def test_rut_repetido(self):
        r = self.client.post(reverse('personal_funcionario_nuevo'), self.datos_nuevo(rut=self.some.rut))
        self.assertContains(r, 'ya tiene una cuenta')

    def test_tres_claves_incorrectas_cierran_la_sesion(self):
        url = reverse('personal_funcionario_nuevo')
        r = self.client.post(url, self.datos_nuevo(clave_admin='mala'))
        self.assertContains(r, 'Te quedan 2 intento')
        self.client.post(url, self.datos_nuevo(clave_admin='mala'))
        r = self.client.post(url, self.datos_nuevo(clave_admin='mala'))
        self.assertRedirects(r, reverse('personal_ingresar'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(Usuario.objects.filter(rut='32000020-3').exists())
        self.assertEqual(RegistroAuditoria.objects.filter(accion=Accion.REAUTENTICACION_FALLIDA).count(), 3)
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.SESION_CERRADA, actor=self.admin).exists())

    def test_una_clave_correcta_reinicia_los_intentos(self):
        url = reverse('personal_funcionario_nuevo')
        self.client.post(url, self.datos_nuevo(clave_admin='mala'))
        self.client.post(url, self.datos_nuevo(clave_admin='mala'))
        self.client.post(url, self.datos_nuevo())  # correcta
        self.assertEqual(self.client.session.get('reautenticacion_fallida'), 0)

    def accion(self, usuario, accion, clave=None):
        return self.client.post(reverse('personal_funcionario_accion', args=[usuario.pk, accion]),
                                {'clave_admin': clave or self.clave_admin, 'motivo': 'Término de contrato'})

    def test_desactivar_impide_ingresar_y_reactivar(self):
        self.accion(self.some, 'desactivar')
        self.some.refresh_from_db()
        self.assertFalse(self.some.is_active)
        self.assertTrue(RegistroAuditoria.objects.filter(accion=Accion.DESACTIVACION, objetivo=self.some,
                                                         detalle='Término de contrato').exists())
        self.client.logout()
        self.assertContains(self.ingresar(self.some), 'RUT o clave incorrectos')
        self.ingresar(self.admin)
        self.accion(self.some, 'reactivar')
        self.some.refresh_from_db()
        self.assertTrue(self.some.is_active)

    def test_no_puede_desactivarse_a_si_mismo_ni_al_ultimo_admin(self):
        self.accion(self.admin, 'desactivar')
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_clave_temporal_desbloquea(self):
        self.some.intentos_fallidos = 3
        self.some.save()
        r = self.accion(self.some, 'clave')
        self.some.refresh_from_db()
        self.assertTrue(self.some.check_password(r.context['clave']))
        self.assertTrue(self.some.debe_cambiar_clave)
        self.assertEqual(self.some.intentos_fallidos, 0)

    def test_pagina_de_auditoria(self):
        self.accion(self.some, 'desactivar')
        r = self.client.get(reverse('personal_auditoria'))
        self.assertContains(r, 'Desactivó un funcionario')
