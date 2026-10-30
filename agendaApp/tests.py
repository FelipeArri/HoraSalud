from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from autenticacionApp.models import Paciente
from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema

from .comandos import ReservarHoraCommand
from .estados_hora import EstadoHora, Hora as HoraDominio, TransicionInvalida
from .models import BloqueHorario, Hora


def nueva_hora():
    return HoraDominio(id_hora="h1", id_bloque=1, id_paciente="p1")


class HoraTests(SimpleTestCase):
    def test_nace_reservada(self):
        self.assertEqual(nueva_hora().estado, EstadoHora.RESERVADA)

    def test_no_show_solo_desde_confirmada(self):
        # RF-05
        hora = nueva_hora()
        with self.assertRaises(TransicionInvalida):
            hora.marcar_no_show()
        hora.confirmar()
        hora.marcar_no_show()
        self.assertEqual(hora.estado, EstadoHora.NO_SHOW)

    def test_cancelacion_exige_motivo(self):
        # RN-05
        hora = nueva_hora()
        with self.assertRaises(TransicionInvalida):
            hora.cancelar('   ')
        hora.cancelar('Paciente avisa que no puede asistir')
        self.assertEqual(hora.motivo_cancelacion, 'Paciente avisa que no puede asistir')

    def test_reasignar_solo_no_show_o_cancelada(self):
        # RF-06
        hora = nueva_hora()
        with self.assertRaises(TransicionInvalida):
            hora.reasignar('p2')
        hora.cancelar('motivo')
        hora.reasignar('p2')
        self.assertEqual((hora.id_paciente, hora.estado), ('p2', EstadoHora.REASIGNADA))


class Bloque:
    def __init__(self, estado):
        self.estado = estado


class RepositorioBloques:
    def __init__(self, bloques):
        self.bloques = bloques

    def buscar_por_id(self, bloque_id):
        return self.bloques.get(bloque_id)


class RepositorioHoras:
    def crear(self, id_bloque, id_paciente):
        return HoraDominio(id_hora="nueva", id_bloque=id_bloque, id_paciente=id_paciente)


class RegistroAuditoria:
    def __init__(self):
        self.eventos = []

    def registrar(self, **evento):
        self.eventos.append(evento)


class ReservarHoraCommandTests(SimpleTestCase):
    def test_reserva_bloque_disponible_y_audita(self):
        # RF-02 y RN-11
        bloques = RepositorioBloques({1: Bloque('disponible')})
        auditoria = RegistroAuditoria()
        hora = ReservarHoraCommand(bloques, RepositorioHoras(), auditoria, bloque_id=1, paciente_id='p1').ejecutar()
        self.assertEqual(hora.estado, EstadoHora.RESERVADA)
        self.assertEqual(bloques.buscar_por_id(1).estado, 'reservado')
        self.assertEqual(auditoria.eventos[0]['accion'], 'ReservarHora')

    def test_bloque_ya_reservado_se_rechaza(self):
        # RN-02: doble reserva
        bloques = RepositorioBloques({1: Bloque('reservado')})
        comando = ReservarHoraCommand(bloques, RepositorioHoras(), RegistroAuditoria(), bloque_id=1, paciente_id='p2')
        with self.assertRaises(ValueError):
            comando.ejecutar()


class DobleReservaBaseDatosTests(TestCase):
    """RN-01/RN-02 a nivel de base de datos: una sola hora vigente por bloque."""

    def setUp(self):
        call_command('cargar_datos_demo', stdout=StringIO())
        self.bloque = BloqueHorario.objects.filter(estado=BloqueHorario.Estado.DISPONIBLE).first()
        self.paciente_1, self.paciente_2 = Paciente.objects.all()[:2]

    def test_segunda_hora_vigente_en_el_mismo_bloque_se_rechaza(self):
        Hora.objects.create(bloque=self.bloque, paciente=self.paciente_1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Hora.objects.create(bloque=self.bloque, paciente=self.paciente_2)

    def test_tras_cancelar_el_bloque_se_puede_volver_a_reservar(self):
        hora = Hora.objects.create(bloque=self.bloque, paciente=self.paciente_1)
        hora.estado = Hora.Estado.CANCELADA
        hora.motivo_cancelacion = 'Prueba'
        hora.save()
        Hora.objects.create(bloque=self.bloque, paciente=self.paciente_2)
        self.assertEqual(Hora.objects.filter(bloque=self.bloque).count(), 2)

    def test_datos_demo_no_se_duplican(self):
        antes = Hora.objects.count()
        call_command('cargar_datos_demo', stdout=StringIO())
        self.assertEqual(Hora.objects.count(), antes)


class ConfiguracionSistemaTests(SimpleTestCase):
    def test_es_unica_y_trae_los_parametros_del_negocio(self):
        # Singleton
        self.assertIs(ConfiguracionSistema(), ConfiguracionSistema())
        self.assertEqual(ConfiguracionSistema().tolerancia_no_show_minutos, 20)
        self.assertEqual(ConfiguracionSistema().horizonte_maximo_reserva_dias, 30)
