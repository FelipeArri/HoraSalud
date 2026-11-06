"""Pruebas de B-21: plantilla semanal, ausencias, ventanilla/sobrecupo y próximo control."""
from datetime import time, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacionApp.models import Paciente, Profesional, RegistroAuditoria, Usuario
from listaEsperaApp.models import EsperaPaciente

from . import gestion_agendas as ga
from . import servicios
from .models import Agenda, AusenciaProfesional, BloqueHorario, Hora, IndicacionControl, PlantillaAgenda

Tipo = BloqueHorario.TipoCupo


def proximo(dia_semana, desde=None):
    """Próxima fecha (desde mañana) que cae en ese día de la semana."""
    dia = (desde or timezone.localdate()) + timedelta(days=1)
    while dia.weekday() != dia_semana:
        dia += timedelta(days=1)
    return dia


class Base(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.prof = Profesional.objects.select_related('especialidad').get(
            especialidad__tipo='medicina_general')
        self.paciente = Paciente.objects.select_related('usuario').filter(
            horas__isnull=True).first() or Paciente.objects.first()
        self.paciente.prevision_consultada_en = timezone.now()  # no consultar FONASA en cada prueba
        self.paciente.save()


class PlantillaTests(Base):
    def test_generar_crea_bloques_segun_plantilla_sin_duplicar(self):
        PlantillaAgenda.objects.filter(profesional=self.prof).delete()
        plantilla = PlantillaAgenda.objects.create(profesional=self.prof, especialidad=self.prof.especialidad,
                                                   dia_semana=2, hora_inicio=time(14, 0), hora_fin=time(16, 0),
                                                   duracion_min=30)
        creados = ga.generar_agendas(semanas=2, profesional=self.prof)
        self.assertEqual(creados, 2 * 4)  # 2 miércoles x 4 bloques de 30 min
        miercoles = proximo(2)
        horas = list(BloqueHorario.objects.filter(agenda__profesional=self.prof, agenda__fecha=miercoles,
                                                  hora_inicio__gte=time(14, 0)).values_list('hora_inicio', flat=True))
        self.assertEqual(horas, [time(14, 0), time(14, 30), time(15, 0), time(15, 30)])
        self.assertEqual(ga.generar_agendas(semanas=2, profesional=self.prof), 0)  # no duplica
        self.assertIn('Lunes', str(PlantillaAgenda(profesional=self.prof, especialidad=self.prof.especialidad,
                                                   dia_semana=0, hora_inicio=time(8), hora_fin=time(9))))
        self.assertTrue(plantilla.activa)

    def test_plantillas_que_se_cruzan_se_rechazan(self):
        cruce = PlantillaAgenda(profesional=self.prof, especialidad=self.prof.especialidad, dia_semana=0,
                                hora_inicio=time(11, 0), hora_fin=time(12, 30))
        with self.assertRaises(servicios.ReglaNegocioError):
            ga.validar_plantilla(cruce)

    def test_duplicar_semana_anterior(self):
        lunes = ga.lunes_de(timezone.localdate()) + timedelta(days=14)
        antes = BloqueHorario.objects.filter(agenda__profesional=self.prof,
                                             agenda__fecha__range=(lunes, lunes + timedelta(days=6))).count()
        origen = lunes - timedelta(days=7)
        agenda = Agenda.objects.create(profesional=self.prof, especialidad=self.prof.especialidad, fecha=origen)
        BloqueHorario.objects.create(agenda=agenda, hora_inicio=time(15), hora_fin=time(15, 20))
        BloqueHorario.objects.create(agenda=agenda, hora_inicio=time(16), hora_fin=time(16, 20), tipo_cupo=Tipo.SOBRECUPO)
        creados = ga.duplicar_semana_anterior(self.prof, lunes)
        self.assertGreaterEqual(creados, 1)
        copiado = BloqueHorario.objects.filter(agenda__profesional=self.prof, agenda__fecha=lunes)
        self.assertTrue(copiado.filter(hora_inicio=time(15)).exists())
        self.assertFalse(copiado.filter(tipo_cupo=Tipo.SOBRECUPO).exists())  # sobrecupos no se copian
        self.assertGreater(copiado.count() + antes, antes)


class AppPacienteTests(Base):
    def test_cupos_de_ventanilla_no_se_ven_ni_se_reservan_en_la_app(self):
        libres = servicios.bloques_reservables(self.prof.especialidad)
        self.assertTrue(libres)
        self.assertTrue(all(b.tipo_cupo == Tipo.PROGRAMADO for b in libres))
        morbilidad = BloqueHorario.objects.filter(agenda__profesional=self.prof, tipo_cupo=Tipo.MORBILIDAD,
                                                  agenda__fecha__gt=timezone.localdate()).first()
        self.assertIsNotNone(morbilidad)
        with self.assertRaisesMessage(servicios.ReglaNegocioError, 'solo en el SOME'):
            servicios.reservar_hora(self.paciente, morbilidad.pk)


class AusenciaTests(Base):
    def test_ausencia_bloquea_suspende_avisa_y_da_prioridad(self):
        dia = BloqueHorario.objects.filter(agenda__profesional=self.prof, hora_vigente__isnull=False,
                                           agenda__fecha__gt=timezone.localdate()).first().agenda.fecha
        horas = list(Hora.objects.filter(bloque__agenda__profesional=self.prof, bloque__agenda__fecha=dia,
                                         estado__in=servicios.ESTADOS_VIGENTES))
        self.assertTrue(horas)
        resultado = ga.registrar_ausencia(self.prof, dia, dia, AusenciaProfesional.Motivo.IMPREVISTA)
        self.assertEqual(resultado.horas_suspendidas, len(horas))
        self.assertFalse(BloqueHorario.objects.filter(agenda__profesional=self.prof, agenda__fecha=dia)
                         .exclude(estado=BloqueHorario.Estado.BLOQUEADO).exists())
        hora = Hora.objects.get(pk=horas[0].pk)
        self.assertEqual(hora.estado, Hora.Estado.SUSPENDIDA)
        self.assertIn('profesional ausente', hora.motivo_cancelacion)
        self.assertIsNone(hora.bloque_activo)
        primero = EsperaPaciente.objects.filter(especialidad=self.prof.especialidad).order_by('orden').first()
        self.assertIn(primero.paciente_id, {h.paciente_id for h in horas})
        # El paciente ve el aviso en su inicio
        self.client.force_login(hora.paciente.usuario)
        if hora.paciente.usuario.tipo_usuario == Usuario.Tipo.TUTOR:
            return
        r = self.client.get(reverse('mi_inicio'))
        self.assertContains(r, 'El CESFAM suspendió tu hora')
        # Generar agendas no recrea bloques en días de ausencia
        self.assertEqual(ga.generar_agendas(desde=dia, semanas=1, profesional=self.prof) >= 0, True)
        self.assertFalse(BloqueHorario.objects.filter(agenda__profesional=self.prof, agenda__fecha=dia,
                                                      estado=BloqueHorario.Estado.DISPONIBLE).exists())


class VentanillaTests(Base):
    def setUp(self):
        super().setUp()
        # Un día en que el paciente NO tenga ya una hora vigente (los datos demo a veces le asignan una)
        dias_ocupados = Hora.objects.filter(paciente=self.paciente, estado__in=servicios.ESTADOS_VIGENTES) \
            .values_list('bloque__agenda__fecha', flat=True)
        self.agenda = (Agenda.objects.filter(profesional=self.prof, fecha__gt=timezone.localdate())
                       .exclude(fecha__in=list(dias_ocupados)).first())

    def test_dar_hora_de_morbilidad_en_ventanilla(self):
        bloque = self.agenda.bloques.filter(tipo_cupo=Tipo.MORBILIDAD, estado='disponible').first()
        hora = ga.dar_hora_ventanilla(self.paciente, bloque.pk)
        self.assertEqual(hora.estado, Hora.Estado.CONFIRMADA)
        with self.assertRaises(servicios.ReglaNegocioError):  # mismo día y especialidad
            ga.dar_hora_ventanilla(self.paciente, self.agenda.bloques.filter(estado='disponible').first().pk)

    def test_sobrecupo_crea_bloque_extra_que_no_se_ve_en_la_app(self):
        hora = ga.dar_sobrecupo(self.paciente, self.agenda, time(13, 0))
        self.assertEqual(hora.bloque.tipo_cupo, Tipo.SOBRECUPO)
        self.assertNotIn(hora.bloque, servicios.bloques_reservables(self.prof.especialidad))
        otro = Paciente.objects.exclude(pk=self.paciente.pk).first()
        with self.assertRaisesMessage(servicios.ReglaNegocioError, 'Ya existe un bloque'):
            ga.dar_sobrecupo(otro, self.agenda, time(13, 0))

    def test_pantalla_ventanilla_y_auditoria(self):
        some = Usuario.objects.get(username__startswith='demo_', tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(some)
        url = (f"{reverse('some_ventanilla')}?rut={self.paciente.usuario.rut}&fecha={self.agenda.fecha:%Y-%m-%d}"
               f"&profesional={self.prof.pk}")
        r = self.client.get(url)
        self.assertContains(r, 'Dar sobrecupo')
        r = self.client.post(url, {'agenda': self.agenda.pk, 'hora_inicio': '13:00'})
        self.assertRedirects(r, reverse('some_nomina'), fetch_redirect_response=False)
        self.assertTrue(RegistroAuditoria.objects.filter(accion='sobrecupo', actor=some).exists())

    def test_paciente_no_vigente_no_recibe_sobrecupo(self):
        self.paciente.estado_inscripcion = Paciente.Estado.NO_VIGENTE
        self.paciente.save()
        with self.assertRaises(servicios.ReglaNegocioError):
            ga.dar_sobrecupo(self.paciente, self.agenda, time(13, 0))


class ProximoControlTests(Base):
    def setUp(self):
        super().setUp()
        hoy = timezone.localdate()
        agenda, _ = Agenda.objects.get_or_create(profesional=self.prof, especialidad=self.prof.especialidad, fecha=hoy)
        bloque = BloqueHorario.objects.create(agenda=agenda, hora_inicio=time(6, 0), hora_fin=time(6, 20))
        self.atendida = Hora.objects.create(bloque=bloque, paciente=self.paciente, estado=Hora.Estado.ATENDIDA)
        ga.generar_agendas(semanas=6, profesional=self.prof)
        self.client.force_login(self.prof.usuario)

    def test_profesional_agenda_el_control_mas_alla_del_horizonte_de_la_app(self):
        Hora.objects.filter(paciente=self.paciente).exclude(pk=self.atendida.pk).delete()
        lejano = BloqueHorario.objects.filter(agenda__profesional=self.prof, estado='disponible',
                                              tipo_cupo=Tipo.PROGRAMADO,
                                              agenda__fecha__gt=timezone.localdate() + timedelta(days=31)).first()
        self.assertIsNotNone(lejano)
        r = self.client.post(reverse('profesional_control', args=[self.atendida.pk]), {'bloque': lejano.pk})
        self.assertRedirects(r, reverse('profesional_agenda'), fetch_redirect_response=False)
        self.assertTrue(Hora.objects.filter(paciente=self.paciente, bloque=lejano).exists())

    def test_indicar_control_aparece_en_la_app_y_se_resuelve_al_reservar(self):
        Hora.objects.filter(paciente=self.paciente).exclude(pk=self.atendida.pk).delete()
        self.client.post(reverse('profesional_control', args=[self.atendida.pk]), {'accion': 'indicar', 'semanas': 2})
        indicacion = IndicacionControl.objects.get(paciente=self.paciente)
        self.assertEqual(indicacion.fecha_sugerida, timezone.localdate() + timedelta(weeks=2))
        self.client.force_login(self.paciente.usuario)
        self.assertContains(self.client.get(reverse('mi_inicio')), 'te indicó un control')
        servicios.reservar_hora(self.paciente, servicios.bloques_reservables(self.prof.especialidad)[0].pk)
        indicacion.refresh_from_db()
        self.assertIsNotNone(indicacion.resuelta_en)

    def test_otro_profesional_no_puede_tocar_la_hora(self):
        otro = Profesional.objects.exclude(pk=self.prof.pk).first()
        self.client.force_login(otro.usuario)
        self.assertEqual(self.client.get(reverse('profesional_control', args=[self.atendida.pk])).status_code, 404)


class PantallasTests(Base):
    def test_calendario_semanal_por_rol(self):
        admin_o_some = Usuario.objects.get(username__startswith='demo_', tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(admin_o_some)
        r = self.client.get(reverse('agendas_semana'), {'profesional': self.prof.pk})
        self.assertContains(r, 'Agenda semanal')
        self.assertContains(r, 'Ventanilla / sobrecupo')
        self.assertNotContains(r, 'Duplicar')  # el SOME no modifica agendas (P-07)
        self.client.force_login(self.paciente.usuario)
        self.assertRedirects(self.client.get(reverse('agendas_semana')), reverse('inicio'),
                             fetch_redirect_response=False)

    def test_administrador_ve_herramientas_de_direccion(self):
        admin = Usuario.objects.create(username='adm_test', rut='32000001-7', tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        self.client.force_login(admin)
        r = self.client.get(reverse('agendas_semana'), {'profesional': self.prof.pk})
        self.assertContains(r, 'Duplicar en esta semana')
        self.assertEqual(self.client.get(reverse('agendas_plantillas', args=[self.prof.pk])).status_code, 200)
        r = self.client.post(reverse('agendas_ausencias'), {
            'profesional': self.prof.pk, 'desde': proximo(3), 'hasta': proximo(3), 'motivo': 'capacitacion'})
        self.assertRedirects(r, reverse('agendas_ausencias'), fetch_redirect_response=False)
        self.assertTrue(RegistroAuditoria.objects.filter(accion='ausencia', actor=admin).exists())
