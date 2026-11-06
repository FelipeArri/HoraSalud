"""Pruebas de B-10: vínculo de tutor autorizado por el paciente o por el SOME (RF-03, RN-11)."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Paciente, RegistroAuditoria, Usuario
from .sesion import CLAVE_PACIENTE
from .test_entrega_codigo import ISAPRE, NUEVA_FONASA
from .validators import calcular_dv


def rut(cuerpo):
    return f'{cuerpo}-{calcular_dv(cuerpo)}'


RUT_TUTOR_NUEVO = rut(32000001)
ACCION = RegistroAuditoria.Accion


class Base(TestCase):
    databases = {'default', 'fonasa'}  # el SOME también consulta el padrón FONASA simulado

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.sin_tutor = Paciente.objects.filter(tutor__isnull=True).select_related('usuario').first()
        self.con_tutor = Paciente.objects.filter(tutor__isnull=False).select_related('usuario', 'tutor').first()
        self.tutor_demo = self.con_tutor.tutor
        self.some = Usuario.objects.get(tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)

    def autorizar(self, rut_tutor, nombres='Ana', apellidos='Pérez Soto', confirmo=True):
        datos = {'rut': rut_tutor, 'nombres': nombres, 'apellidos': apellidos}
        if confirmo:
            datos['confirmo'] = 'on'
        return self.client.post(reverse('autorizar_tutor'), datos)


class PacienteAutorizaTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.sin_tutor.usuario)

    def test_mis_datos_muestra_formulario_de_tutor(self):
        self.assertContains(self.client.get(reverse('mis_datos')), 'Autorizar tutor')

    def test_autoriza_tutor_nuevo_sin_clave_y_queda_auditado(self):
        respuesta = self.autorizar(RUT_TUTOR_NUEVO)
        self.assertRedirects(respuesta, reverse('mis_datos'), fetch_redirect_response=False)
        self.sin_tutor.refresh_from_db()
        tutor = self.sin_tutor.tutor
        self.assertEqual((tutor.rut, tutor.tipo_usuario), (RUT_TUTOR_NUEVO, Usuario.Tipo.TUTOR))
        self.assertFalse(tutor.has_usable_password())  # solo entra con huella, tras el enrolamiento en el SOME
        registro = RegistroAuditoria.objects.get(accion=ACCION.TUTOR_AUTORIZADO)
        self.assertEqual(registro.actor, self.sin_tutor.usuario)
        self.assertIn('paciente desde la app', registro.detalle)
        self.assertContains(self.client.get(reverse('mis_datos')), 'debe activar su huella')

    def test_autoriza_tutor_existente_solo_con_rut(self):
        self.autorizar(self.tutor_demo.rut, nombres='', apellidos='')
        self.sin_tutor.refresh_from_db()
        self.assertEqual(self.sin_tutor.tutor, self.tutor_demo)

    def test_rechazos(self):
        otro_paciente = Paciente.objects.exclude(pk=self.sin_tutor.pk).first().usuario
        casos = [
            (self.sin_tutor.usuario.rut, 'propio tutor'),
            (otro_paciente.rut, 'otro tipo de cuenta'),
            (self.some.rut, 'otro tipo de cuenta'),
            ('12345678-0', 'Revisa tu RUT'),
        ]
        for rut_tutor, texto in casos:
            self.assertContains(self.autorizar(rut_tutor), texto, msg_prefix=rut_tutor)
        self.assertContains(self.autorizar(RUT_TUTOR_NUEVO, nombres='', apellidos=''), 'nombres y apellidos')
        self.assertContains(self.autorizar(RUT_TUTOR_NUEVO, confirmo=False), 'Confirma que autorizas')
        self.sin_tutor.refresh_from_db()
        self.assertIsNone(self.sin_tutor.tutor)
        self.assertFalse(Usuario.objects.filter(rut=RUT_TUTOR_NUEVO).exists())
        self.assertFalse(RegistroAuditoria.objects.filter(accion=ACCION.TUTOR_AUTORIZADO).exists())

    def test_si_ya_tiene_tutor_debe_quitarlo_primero(self):
        self.autorizar(self.tutor_demo.rut)
        self.assertContains(self.client.post(reverse('autorizar_tutor'), {
            'rut': RUT_TUTOR_NUEVO, 'nombres': 'Ana', 'apellidos': 'Pérez', 'confirmo': 'on'}, follow=True),
            'Ya tienes un tutor')
        self.sin_tutor.refresh_from_db()
        self.assertEqual(self.sin_tutor.tutor, self.tutor_demo)


class PacienteQuitaTests(Base):
    def test_quitar_tutor_corta_el_acceso_del_tutor(self):
        # El tutor está actuando por el paciente
        self.client.force_login(self.tutor_demo)
        sesion = self.client.session
        sesion[CLAVE_PACIENTE] = str(self.con_tutor.pk)
        sesion.save()
        self.assertEqual(self.client.get(reverse('mi_inicio')).status_code, 200)

        # El paciente lo quita desde su propia sesión (otro navegador)
        paciente = self.client_class()
        paciente.defaults['HTTP_HOST'] = 'localhost'
        paciente.force_login(self.con_tutor.usuario)
        self.assertRedirects(paciente.post(reverse('quitar_tutor')), reverse('mis_datos'))
        self.con_tutor.refresh_from_db()
        self.assertIsNone(self.con_tutor.tutor)
        self.assertTrue(RegistroAuditoria.objects.filter(accion=ACCION.TUTOR_REVOCADO,
                                                         objetivo=self.con_tutor.usuario).exists())

        # En su siguiente clic, el tutor ya no puede actuar por esa persona (OWASP A01)
        self.assertRedirects(self.client.get(reverse('mi_inicio')), reverse('elegir_paciente'))

    def test_el_tutor_no_puede_autorizarse_ni_quitarse(self):
        self.client.force_login(self.tutor_demo)
        self.client.post(reverse('quitar_tutor'))
        self.autorizar(RUT_TUTOR_NUEVO)
        self.con_tutor.refresh_from_db()
        self.assertEqual(self.con_tutor.tutor, self.tutor_demo)
        self.assertFalse(Usuario.objects.filter(rut=RUT_TUTOR_NUEVO).exists())

    def test_tutor_ve_a_quien_tiene_a_cargo(self):
        self.client.force_login(self.tutor_demo)
        self.assertContains(self.client.get(reverse('mis_datos')), self.con_tutor.usuario.rut)


class SomeTutoresTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.some)

    def autorizar_some(self, rut_paciente, rut_tutor, confirmo=True):
        datos = {'rut': rut_paciente, 'accion': 'autorizar', 'tutor-rut': rut_tutor,
                 'tutor-nombres': 'Luis', 'tutor-apellidos': 'Rojas Díaz'}
        if confirmo:
            datos['tutor-confirmo'] = 'on'
        return self.client.post(reverse('some_tutores'), datos)

    def test_solo_el_some_entra(self):
        self.client.force_login(self.sin_tutor.usuario)
        self.assertRedirects(self.client.get(reverse('some_tutores')), reverse('inicio'))

    def test_consulta_muestra_el_tutor_actual(self):
        respuesta = self.client.get(reverse('some_tutores'), {'rut': self.con_tutor.usuario.rut})
        self.assertContains(respuesta, self.tutor_demo.rut)
        self.assertContains(respuesta, 'Quitar tutor')

    def test_autoriza_en_persona_y_queda_auditado(self):
        respuesta = self.autorizar_some(self.sin_tutor.usuario.rut, RUT_TUTOR_NUEVO)
        self.assertRedirects(respuesta, f"{reverse('some_tutores')}?rut={self.sin_tutor.usuario.rut}")
        self.sin_tutor.refresh_from_db()
        self.assertEqual(self.sin_tutor.tutor.rut, RUT_TUTOR_NUEVO)
        registro = RegistroAuditoria.objects.get(accion=ACCION.TUTOR_AUTORIZADO)
        self.assertEqual(registro.actor, self.some)
        self.assertIn('SOME en persona', registro.detalle)

    def test_exige_confirmar_la_autorizacion_del_paciente(self):
        self.assertContains(self.autorizar_some(self.sin_tutor.usuario.rut, RUT_TUTOR_NUEVO, confirmo=False),
                            'Confirma que el paciente')
        self.sin_tutor.refresh_from_db()
        self.assertIsNone(self.sin_tutor.tutor)

    def test_menor_sin_cuenta_se_registra_al_autorizar(self):
        self.assertFalse(Usuario.objects.filter(rut=NUEVA_FONASA).exists())
        self.autorizar_some(NUEVA_FONASA, self.tutor_demo.rut)
        paciente = Paciente.objects.get(usuario__rut=NUEVA_FONASA)
        self.assertEqual(paciente.tutor, self.tutor_demo)

    def test_rechaza_paciente_que_no_pertenece_al_cesfam(self):
        self.assertContains(self.client.get(reverse('some_tutores'), {'rut': ISAPRE}), 'ISAPRE')
        self.autorizar_some(ISAPRE, RUT_TUTOR_NUEVO)
        self.assertFalse(Usuario.objects.filter(rut__in=[ISAPRE, RUT_TUTOR_NUEVO]).exists())

    def test_rechaza_rut_de_tutor_como_paciente(self):
        self.assertContains(self.client.get(reverse('some_tutores'), {'rut': self.tutor_demo.rut}),
                            'no de un paciente')

    def test_quita_tutor(self):
        rut_paciente = self.con_tutor.usuario.rut
        self.client.post(reverse('some_tutores'), {'rut': rut_paciente, 'accion': 'quitar'})
        self.con_tutor.refresh_from_db()
        self.assertIsNone(self.con_tutor.tutor)
        self.assertIn('SOME en persona', RegistroAuditoria.objects.get(accion=ACCION.TUTOR_REVOCADO).detalle)
