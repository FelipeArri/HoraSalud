"""
Pruebas de B-14: lista de espera con tramos (RF-06, RN-17), avisos push y app instalable.

El reloj se fija con mock (AHORA = mañana a las 10:00) para que las pruebas no
dependan de la hora en que se ejecutan.
"""
import json
import tempfile
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from agendaApp import servicios as agenda
from agendaApp.models import Agenda, BloqueHorario, Especialidad, Hora
from autenticacionApp import privacidad
from autenticacionApp.models import Paciente, Profesional, RegistroAuditoria, Sector, Usuario
from notificacionesApp.models import RegistroNotificacion, SuscripcionPush

from . import servicios
from .models import CupoLiberado, EsperaPaciente, OfertaCupo

Estado = OfertaCupo.Estado
Resultado = CupoLiberado.Resultado


def rut_valido(numero):
    suma, factor = 0, 2
    for digito in reversed(str(numero)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    dv = 11 - suma % 11
    return f'{numero}-{"0" if dv == 11 else "K" if dv == 10 else dv}'


HOY = timezone.localdate()  # fecha real, tomada antes de fijar el reloj


def a_las(hora, minuto=0, dias=1):
    """Fecha y hora local (por defecto mañana) como datetime con zona horaria."""
    fecha = HOY + timedelta(days=dias)
    return timezone.make_aware(datetime.combine(fecha, time(hora, minuto)))


AHORA = a_las(10)


@override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=False, VAPID_PUBLIC_KEY='', VAPID_PRIVATE_KEY='')
class Base(TestCase):
    databases = {'default', 'fonasa'}

    def setUp(self):
        self.reloj = mock.patch('django.utils.timezone.now', return_value=AHORA)
        self.reloj.start()
        self.addCleanup(self.reloj.stop)
        self.especialidad = Especialidad.objects.create(nombre='Kinesiología', tipo=Especialidad.Tipo.PROGRAMA)
        usuario_prof = Usuario.objects.create(username='kine', rut=rut_valido(31000001), first_name='Ana',
                                              last_name='Kine', tipo_usuario=Usuario.Tipo.PROFESIONAL)
        self.prof = Profesional.objects.create(usuario=usuario_prof, especialidad=self.especialidad, box_atencion='7')
        self.pacientes = [self.crear_paciente(i) for i in range(1, 5)]
        self.p0, self.p1, self.p2, self.p3 = self.pacientes

    def crear_paciente(self, n, sector=None):
        usuario = Usuario.objects.create(username=f'pac{n}', rut=rut_valido(30500000 + n), first_name=f'Paciente{n}',
                                         last_name='Prueba', telefono='+56911111111')
        privacidad.registrar(usuario, True)
        return Paciente.objects.create(usuario=usuario, sector=sector, prevision_consultada_en=AHORA)

    def crear_bloque(self, horas_desde_ahora):
        inicio = timezone.localtime(AHORA + timedelta(hours=horas_desde_ahora))
        agenda_dia, _ = Agenda.objects.get_or_create(especialidad=self.especialidad, profesional=self.prof,
                                                     fecha=inicio.date())
        return BloqueHorario.objects.create(agenda=agenda_dia, hora_inicio=inicio.time(),
                                            hora_fin=(inicio + timedelta(minutes=20)).time())

    def inscribir(self, *pacientes):
        return [servicios.inscribir(p, self.especialidad) for p in pacientes]

    def cancelar(self, horas_desde_ahora, quien=None):
        """p0 tiene una hora y la cancela: dispara el Observer (cupo_liberado)."""
        bloque = self.crear_bloque(horas_desde_ahora)
        hora = Hora.objects.create(bloque=bloque, paciente=quien or self.p0)
        agenda.cancelar_hora(hora, 'No puedo asistir ese día')
        bloque.refresh_from_db()
        return bloque

    def oferta_de(self, paciente):
        return OfertaCupo.objects.get(paciente=paciente, estado=Estado.PENDIENTE)

    def cambiar_reloj(self, momento):
        self.reloj.stop()
        self.reloj = mock.patch('django.utils.timezone.now', return_value=momento)
        self.reloj.start()


class TramosTests(Base):
    def test_tramo_segun_anticipacion(self):
        self.assertEqual(servicios.tramo_de(self.crear_bloque(72)), OfertaCupo.Tramo.LARGO)
        self.assertEqual(servicios.tramo_de(self.crear_bloque(32)), OfertaCupo.Tramo.CORTO)
        self.assertEqual(servicios.tramo_de(self.crear_bloque(10)), servicios.VENTANILLA)

    def test_avisos_solo_de_8_a_20(self):
        self.assertTrue(servicios.en_horario_de_avisos(a_las(10), 60))
        self.assertTrue(servicios.en_horario_de_avisos(a_las(19, 50), 10))
        self.assertFalse(servicios.en_horario_de_avisos(a_las(19, 30), 60))  # no alcanza a responder antes de las 20
        self.assertFalse(servicios.en_horario_de_avisos(a_las(7, 30), 10))
        self.assertFalse(servicios.en_horario_de_avisos(a_las(22), 10))

    def test_texto_del_plazo(self):
        self.assertEqual(servicios.texto_plazo(60), '1 hora')
        self.assertEqual(servicios.texto_plazo(10), '10 minutos')


class InscripcionTests(Base):
    def test_se_respeta_el_orden_de_llegada(self):
        e1, e2, e3 = self.inscribir(self.p1, self.p2, self.p3)
        self.assertEqual([servicios.posicion(e) for e in (e1, e2, e3)], [1, 2, 3])
        self.assertTrue(RegistroAuditoria.objects.filter(accion=RegistroAuditoria.Accion.ESPERA_ALTA).exists())

    def test_no_se_inscribe_dos_veces(self):
        self.inscribir(self.p1)
        with self.assertRaises(agenda.ReglaNegocioError):
            servicios.inscribir(self.p1, self.especialidad)

    def test_con_hora_vigente_no_necesita_lista(self):  # RN-01
        Hora.objects.create(bloque=self.crear_bloque(72), paciente=self.p1)
        with self.assertRaises(agenda.ReglaNegocioError):
            servicios.inscribir(self.p1, self.especialidad)

    def test_no_vigente_no_se_inscribe(self):  # RN-16
        self.p1.estado_inscripcion = Paciente.Estado.NO_VIGENTE
        self.p1.save()
        with self.assertRaises(agenda.ReglaNegocioError):
            servicios.inscribir(self.p1, self.especialidad)

    def test_al_conseguir_hora_sale_de_la_lista(self):
        self.inscribir(self.p1)
        Hora.objects.create(bloque=self.crear_bloque(100), paciente=self.p1)
        self.assertFalse(EsperaPaciente.objects.filter(paciente=self.p1).exists())


class TramoLargoTests(Base):
    """Cancelación con más de 48 h: se ofrece en orden, 1 hora para responder."""

    def setUp(self):
        super().setUp()
        self.inscribir(self.p1, self.p2, self.p3)
        self.bloque = self.cancelar(72)

    def test_se_ofrece_al_primero_con_una_hora_de_plazo(self):
        oferta = self.oferta_de(self.p1)
        self.assertEqual((oferta.tramo, oferta.posicion), (OfertaCupo.Tramo.LARGO, 1))
        self.assertEqual(oferta.vence_en, AHORA + timedelta(minutes=60))
        self.assertEqual(self.bloque.estado, BloqueHorario.Estado.EN_OFERTA)
        self.assertEqual(OfertaCupo.objects.count(), 1)  # una persona a la vez

    def test_el_cupo_ofrecido_no_se_ve_en_la_app(self):
        self.assertNotIn(self.bloque, agenda.bloques_reservables(self.especialidad, self.p3))

    def test_aviso_queda_registrado_sin_datos_de_salud(self):
        aviso = RegistroNotificacion.objects.get(paciente=self.p1)
        # sin avisos activados: queda como aviso dentro de HoraSalud (gratis, sin SMS)
        self.assertEqual((aviso.canal, aviso.estado), (RegistroNotificacion.Canal.APP, RegistroNotificacion.Estado.ENVIADA))
        self.assertIn('1 hora', aviso.mensaje)
        self.assertNotIn('Kinesiología', aviso.mensaje)  # Ley 19.628

    def test_no_puedo_conserva_el_lugar_y_pasa_al_siguiente(self):
        servicios.rechazar(self.oferta_de(self.p1).pk)
        self.assertEqual(self.oferta_de(self.p2).posicion, 2)
        espera = EsperaPaciente.objects.get(paciente=self.p1)
        self.assertEqual((servicios.posicion(espera), espera.ofertas_sin_respuesta), (1, 0))

    def test_sin_respuesta_vence_y_pasa_al_siguiente_sin_castigo(self):
        servicios.procesar(AHORA + timedelta(minutes=61))
        self.assertEqual(OfertaCupo.objects.get(paciente=self.p1).estado, Estado.VENCIDA)
        self.assertTrue(OfertaCupo.objects.filter(paciente=self.p2, estado=Estado.PENDIENTE).exists())
        espera = EsperaPaciente.objects.get(paciente=self.p1)
        self.assertEqual((servicios.posicion(espera), espera.ofertas_sin_respuesta), (1, 1))

    def test_aceptar_reasigna_la_hora(self):
        servicios.rechazar(self.oferta_de(self.p1).pk)
        hora = servicios.aceptar(self.oferta_de(self.p2).pk)
        self.bloque.refresh_from_db()
        self.assertEqual((hora.paciente, hora.bloque), (self.p2, self.bloque))
        self.assertEqual(self.bloque.estado, BloqueHorario.Estado.RESERVADO)
        self.assertFalse(EsperaPaciente.objects.filter(paciente=self.p2).exists())
        self.assertTrue(EsperaPaciente.objects.filter(paciente=self.p1).exists())
        self.assertEqual(CupoLiberado.objects.get().resultado, Resultado.REASIGNADO)
        self.assertTrue(RegistroAuditoria.objects.filter(accion=RegistroAuditoria.Accion.CUPO_ACEPTADO,
                                                         objetivo=self.p2.usuario).exists())

    def test_aceptar_fuera_de_plazo_no_se_puede(self):
        oferta = self.oferta_de(self.p1)
        with self.assertRaisesMessage(agenda.ReglaNegocioError, 'Se acabó el plazo'):
            servicios.aceptar(oferta.pk, ahora=AHORA + timedelta(minutes=61))
        self.assertEqual(OfertaCupo.objects.get(pk=oferta.pk).estado, Estado.VENCIDA)
        self.assertTrue(OfertaCupo.objects.filter(paciente=self.p2, estado=Estado.PENDIENTE).exists())

    def test_doble_clic_o_dos_personas_a_la_vez(self):  # RN-02
        oferta = self.oferta_de(self.p1)
        servicios.aceptar(oferta.pk)
        with self.assertRaises(agenda.ReglaNegocioError):
            servicios.aceptar(oferta.pk)
        self.assertEqual(Hora.objects.filter(bloque=self.bloque, bloque_activo__isnull=False).count(), 1)

    def test_si_el_bloque_ya_fue_tomado_avisa_claro(self):
        oferta = self.oferta_de(self.p1)
        BloqueHorario.objects.filter(pk=self.bloque.pk).update(estado=BloqueHorario.Estado.RESERVADO)
        with self.assertRaisesMessage(agenda.ReglaNegocioError, 'ya fue tomado'):
            servicios.aceptar(oferta.pk)

    def test_si_nadie_lo_toma_queda_libre_en_la_app(self):
        for paciente in (self.p1, self.p2, self.p3):
            servicios.rechazar(self.oferta_de(paciente).pk)
        self.bloque.refresh_from_db()
        self.assertEqual(self.bloque.estado, BloqueHorario.Estado.DISPONIBLE)
        self.assertEqual(self.bloque.tipo_cupo, BloqueHorario.TipoCupo.PROGRAMADO)
        self.assertEqual(CupoLiberado.objects.get().resultado, Resultado.LIBRE_APP)

    def test_salir_de_la_lista_pasa_el_cupo_al_siguiente(self):
        servicios.salir(EsperaPaciente.objects.get(paciente=self.p1))
        self.assertEqual(OfertaCupo.objects.get(paciente=self.p1).estado, Estado.ANULADA)
        self.assertTrue(OfertaCupo.objects.filter(paciente=self.p2, estado=Estado.PENDIENTE).exists())


class OtrosTramosTests(Base):
    def test_entre_24_y_48_horas_da_10_minutos(self):
        self.inscribir(self.p1)
        self.cancelar(32)
        oferta = self.oferta_de(self.p1)
        self.assertEqual(oferta.tramo, OfertaCupo.Tramo.CORTO)
        self.assertEqual(oferta.vence_en, AHORA + timedelta(minutes=10))

    def test_menos_de_24_horas_pasa_a_ventanilla(self):
        self.inscribir(self.p1)
        bloque = self.cancelar(10)
        self.assertEqual((bloque.estado, bloque.tipo_cupo),
                         (BloqueHorario.Estado.DISPONIBLE, BloqueHorario.TipoCupo.LIBERADO))
        self.assertFalse(OfertaCupo.objects.exists())
        self.assertNotIn(bloque, agenda.bloques_reservables(self.especialidad, self.p2))
        self.assertEqual(CupoLiberado.objects.get().resultado, Resultado.VENTANILLA)

    def test_sin_nadie_en_la_fila_todo_sigue_como_antes(self):
        bloque = self.cancelar(72)
        self.assertEqual(bloque.estado, BloqueHorario.Estado.DISPONIBLE)
        self.assertFalse(CupoLiberado.objects.exists())

    def test_de_noche_espera_hasta_las_8(self):
        self.cambiar_reloj(a_las(21))
        self.inscribir(self.p1)
        bloque = self.cancelar(72)
        self.assertEqual(bloque.estado, BloqueHorario.Estado.EN_OFERTA)
        self.assertFalse(OfertaCupo.objects.exists())
        servicios.procesar(a_las(8, 0, dias=2))
        self.assertTrue(OfertaCupo.objects.filter(paciente=self.p1, estado=Estado.PENDIENTE).exists())

    def test_el_tramo_se_recalcula_y_termina_en_ventanilla(self):
        self.inscribir(self.p1, self.p2)
        bloque = self.cancelar(49)
        servicios.procesar(AHORA + timedelta(hours=2))  # venció la de p1; ahora faltan 47 h: 10 minutos
        self.assertEqual(self.oferta_de(self.p2).tramo, OfertaCupo.Tramo.CORTO)
        self.cambiar_reloj(AHORA + timedelta(hours=26))
        servicios.procesar()  # faltan 23 h y no queda nadie: a ventanilla
        bloque.refresh_from_db()
        self.assertEqual(bloque.tipo_cupo, BloqueHorario.TipoCupo.LIBERADO)

    def test_respeta_el_sector_del_profesional(self):  # DEF-06
        sector_a = Sector.objects.create(nombre='Sector A')
        sector_b = Sector.objects.create(nombre='Sector B')
        self.prof.sector = sector_b
        self.prof.save()
        self.p1.sector, self.p2.sector = sector_a, sector_b
        self.p1.save()
        self.p2.save()
        self.inscribir(self.p1, self.p2)
        self.cancelar(72)
        self.assertEqual(self.oferta_de(self.p2).posicion, 2)
        self.assertFalse(OfertaCupo.objects.filter(paciente=self.p1).exists())

    def test_tras_3_ofertas_sin_respuesta_el_some_ve_la_marca(self):
        self.inscribir(self.p1)
        for i in range(3):
            self.cancelar(72 + i, quien=self.pacientes[3])
            servicios.procesar(AHORA + timedelta(minutes=61))
            Hora.objects.filter(paciente=self.p3).delete()
        espera = EsperaPaciente.objects.get(paciente=self.p1)
        self.assertEqual((espera.ofertas_sin_respuesta, servicios.posicion(espera)), (3, 1))  # no pierde su lugar
        some = Usuario.objects.create(username='some', rut=rut_valido(32100001), tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)
        self.client.force_login(some)
        respuesta = self.client.get(reverse('some_lista_espera') + f'?especialidad={self.especialidad.pk}')
        self.assertContains(respuesta, 'Llamar')

    def test_indicadores_cuentan_por_tramo_y_anticipacion(self):
        self.inscribir(self.p1)
        servicios.aceptar(OfertaCupo.objects.get(cupo=CupoLiberado.objects.get(
            bloque=self.cancelar(72))).pk, ahora=AHORA + timedelta(minutes=5))
        datos = servicios.indicadores()
        largo = datos['por_tramo'][0].datos
        self.assertEqual((largo['total'], largo['aceptada'], largo['pct_aceptadas'], largo['demora_min']),
                         (1, 1, 100, 5.0))
        self.assertEqual(datos['pct_reasignados'], 100)


class PantallasTests(Base):
    def setUp(self):
        super().setUp()
        self.some = Usuario.objects.create(username='some', rut=rut_valido(32100001),
                                           tipo_usuario=Usuario.Tipo.ADMINISTRATIVO)

    def test_paciente_se_inscribe_cuando_no_hay_horas(self):
        self.client.force_login(self.p1.usuario)
        pagina = self.client.get(reverse('pedir_bloque', args=[self.especialidad.pk]))
        self.assertContains(pagina, 'Avísame si se libera una hora')
        self.client.post(reverse('inscribirme_lista', args=[self.especialidad.pk]))
        self.assertEqual(EsperaPaciente.objects.get(paciente=self.p1).inscrito_por, EsperaPaciente.Origen.APP)
        self.assertContains(self.client.get(reverse('mi_lista_espera')), 'Lugar 1 de 1')

    def test_paciente_acepta_desde_la_oferta(self):
        self.inscribir(self.p1)
        self.cancelar(72)
        oferta = self.oferta_de(self.p1)
        self.client.force_login(self.p1.usuario)
        self.assertContains(self.client.get(reverse('mi_inicio')), 'Se liberó una hora para ti')
        self.assertContains(self.client.get(reverse('oferta_cupo', args=[oferta.pk])), 'Sí, quiero esta hora')
        respuesta = self.client.post(reverse('oferta_cupo', args=[oferta.pk]), {'accion': 'aceptar'})
        hora = Hora.objects.get(paciente=self.p1, estado=Hora.Estado.RESERVADA)
        self.assertRedirects(respuesta, reverse('hora_lista', args=[hora.pk]))

    def test_nadie_ve_la_oferta_de_otro(self):  # RN-07
        self.inscribir(self.p1)
        self.cancelar(72)
        self.client.force_login(self.p2.usuario)
        self.assertEqual(self.client.get(reverse('oferta_cupo', args=[self.oferta_de(self.p1).pk])).status_code, 404)

    def test_tutor_acepta_por_su_dependiente(self):
        tutor = Usuario.objects.create(username='tutor', rut=rut_valido(32200001), tipo_usuario=Usuario.Tipo.TUTOR)
        privacidad.registrar(tutor, True)
        self.p1.tutor = tutor
        self.p1.save()
        self.inscribir(self.p1)
        self.cancelar(72)
        self.client.force_login(tutor)
        sesion = self.client.session
        sesion['paciente_activo_id'] = str(self.p1.pk)
        sesion.save()
        self.client.post(reverse('oferta_cupo', args=[self.oferta_de(self.p1).pk]), {'accion': 'aceptar'})
        self.assertEqual(OfertaCupo.objects.get(paciente=self.p1).respondida_por, 'Tutor')

    def test_some_inscribe_en_ventanilla_y_acepta_por_telefono(self):
        self.client.force_login(self.some)
        url = reverse('some_lista_espera') + f'?especialidad={self.especialidad.pk}'
        self.client.post(url, {'rut': self.p1.usuario.rut})
        self.assertEqual(EsperaPaciente.objects.get(paciente=self.p1).inscrito_por, EsperaPaciente.Origen.SOME)
        self.cancelar(72)
        pagina = self.client.get(url)
        self.assertContains(pagina, 'Aceptó por teléfono')
        self.client.post(reverse('some_oferta', args=[self.oferta_de(self.p1).pk, 'aceptar']))
        self.assertEqual(OfertaCupo.objects.get(paciente=self.p1).respondida_por, 'SOME (por teléfono)')

    def test_some_ve_los_cupos_liberados_de_ventanilla(self):
        self.inscribir(self.p1)
        self.cancelar(10)
        self.client.force_login(self.some)
        self.assertContains(self.client.get(reverse('some_lista_espera')), 'Entregar en ventanilla')

    def test_indicadores_solo_para_el_administrador(self):
        self.client.force_login(self.p1.usuario)
        self.assertEqual(self.client.get(reverse('indicadores_lista')).status_code, 302)
        admin = Usuario.objects.create(username='adm', rut=rut_valido(32300001), tipo_usuario=Usuario.Tipo.ADMINISTRADOR)
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse('indicadores_lista')), 'Respuestas por tramo')

    def test_ayuda_publica(self):
        self.assertContains(self.client.get(reverse('ayuda')), 'no pierdes tu lugar')


@override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=False)
class AppInstalableTests(TestCase):
    def test_manifest_para_instalar(self):
        datos = json.loads(self.client.get(reverse('manifest')).content)
        self.assertEqual((datos['short_name'], datos['display']), ('HoraSalud', 'standalone'))
        self.assertTrue({'192x192', '512x512'} <= {i['sizes'] for i in datos['icons']})

    def test_service_worker_desde_la_raiz(self):
        respuesta = self.client.get('/sw.js')
        self.assertEqual(respuesta['Content-Type'], 'application/javascript')
        self.assertEqual(respuesta['Service-Worker-Allowed'], '/')
        self.assertIn(b"addEventListener('push'", respuesta.content)

    def test_pagina_sin_conexion(self):
        self.assertContains(self.client.get(reverse('sin_conexion')), 'No hay conexión')


@override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=False, VAPID_PUBLIC_KEY='publica', VAPID_PRIVATE_KEY='privada')
class AvisosPushTests(Base):
    FCM = 'https://fcm.googleapis.com/fcm/send/abc123'

    def suscribir(self, usuario, endpoint):
        self.client.force_login(usuario)
        return self.client.post(reverse('avisos_suscribir'), json.dumps(
            {'endpoint': endpoint, 'keys': {'p256dh': 'clave', 'auth': 'secreto'}}), content_type='application/json')

    def test_solo_acepta_servicios_oficiales_de_avisos(self):  # OWASP A10 (SSRF)
        self.assertEqual(self.suscribir(self.p1.usuario, 'https://intranet.cesfam.local/x').status_code, 400)
        self.assertEqual(self.suscribir(self.p1.usuario, 'http://fcm.googleapis.com/x').status_code, 400)
        self.assertEqual(self.suscribir(self.p1.usuario, self.FCM).status_code, 200)
        self.assertEqual(SuscripcionPush.objects.get().usuario, self.p1.usuario)

    def test_suscribir_exige_sesion(self):
        respuesta = self.client.post(reverse('avisos_suscribir'), '{}', content_type='application/json')
        self.assertEqual(respuesta.status_code, 302)

    @mock.patch('pywebpush.webpush')
    def test_oferta_llega_por_push_al_paciente_y_a_su_tutor(self, webpush):
        tutor = Usuario.objects.create(username='tutor', rut=rut_valido(32200001), tipo_usuario=Usuario.Tipo.TUTOR)
        self.p1.tutor = tutor
        self.p1.save()
        self.suscribir(self.p1.usuario, self.FCM)
        self.suscribir(tutor, self.FCM + 'tutor')
        self.inscribir(self.p1)
        self.cancelar(72)
        self.assertEqual(webpush.call_count, 2)
        datos = json.loads(webpush.call_args.kwargs['data'])
        self.assertIn('/lista-espera/oferta/', datos['url'])
        self.assertEqual(webpush.call_args.kwargs['headers'], {'Urgency': 'high'})
        aviso = RegistroNotificacion.objects.get(paciente=self.p1)
        self.assertEqual((aviso.canal, aviso.estado), (RegistroNotificacion.Canal.PUSH, RegistroNotificacion.Estado.ENVIADA))

    @mock.patch('pywebpush.webpush')
    def test_dispositivo_dado_de_baja_se_borra_y_se_usa_respaldo(self, webpush):
        from pywebpush import WebPushException
        webpush.side_effect = WebPushException('Gone', response=mock.Mock(status_code=410))
        self.suscribir(self.p1.usuario, self.FCM)
        self.inscribir(self.p1)
        self.cancelar(72)
        self.assertFalse(SuscripcionPush.objects.exists())
        estados = set(RegistroNotificacion.objects.filter(paciente=self.p1).values_list('canal', 'estado'))
        self.assertEqual(estados, {('push', 'fallida'), ('app', 'enviada')})  # respaldo: visible en la app

    @mock.patch('pywebpush.webpush')
    def test_aviso_de_prueba(self, webpush):
        self.suscribir(self.p1.usuario, self.FCM)
        respuesta = self.client.post(reverse('avisos_prueba'))
        self.assertEqual(json.loads(respuesta.content), {'ok': True, 'entregados': 1})

    @override_settings(VAPID_PUBLIC_KEY='', VAPID_PRIVATE_KEY='')
    def test_sin_claves_el_aviso_de_prueba_explica_que_falta(self):
        self.client.force_login(self.p1.usuario)
        self.assertEqual(self.client.post(reverse('avisos_prueba')).status_code, 503)

    def test_generar_claves_las_agrega_al_env(self):
        with tempfile.TemporaryDirectory() as carpeta, override_settings(BASE_DIR=Path(carpeta), VAPID_PRIVATE_KEY=''):
            call_command('generar_claves_push', stdout=mock.Mock())
            texto = (Path(carpeta) / '.env').read_text(encoding='utf-8')
        self.assertIn('VAPID_PUBLIC_KEY=B', texto)  # punto sin comprimir: empieza con 0x04 -> "B" en base64url
        self.assertIn('VAPID_PRIVATE_KEY=', texto)


@override_settings(HORASALUD_LISTA_ESPERA_AUTOMATICA=True)
class MiddlewareTests(Base):
    def test_las_visitas_revisan_los_plazos(self):
        from django.core.cache import cache
        cache.clear()
        self.inscribir(self.p1, self.p2)
        self.cancelar(72)
        self.cambiar_reloj(AHORA + timedelta(minutes=61))
        self.client.get(reverse('ayuda'))
        self.assertEqual(OfertaCupo.objects.get(paciente=self.p1).estado, Estado.VENCIDA)
        self.assertTrue(OfertaCupo.objects.filter(paciente=self.p2, estado=Estado.PENDIENTE).exists())

    def test_comando_procesar(self):
        salida = mock.Mock()
        call_command('procesar_lista_espera', stdout=salida)
        self.assertIn('Ofertas vencidas', salida.write.call_args.args[0])
