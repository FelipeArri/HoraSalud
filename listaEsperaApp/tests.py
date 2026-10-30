from django.test import SimpleTestCase

from agendaApp.estados_hora import Hora
from notificacionesApp.estrategias import AppStrategy, EmailStrategy, SmsStrategy
from notificacionesApp.notificacion_factory import NotificacionFactory

from .lista_espera import ListaEspera


class Gateway:
    def __init__(self):
        self.enviados = []

    def enviar_sms(self, **datos):
        self.enviados.append(('sms', datos))

    def enviar_correo(self, **datos):
        self.enviados.append(('email', datos))

    def enviar(self, **datos):
        self.enviados.append(('app', datos))


class RepositorioUsuarios:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def buscar_por_id(self, usuario_id):
        return self.usuarios[usuario_id]


def crear_factory(usuarios, gateway):
    return NotificacionFactory(RepositorioUsuarios(usuarios), gateway, gateway, gateway)


class NotificacionFactoryTests(SimpleTestCase):
    def test_elige_el_canal_segun_los_datos_del_paciente(self):
        # Factory Method + Strategy (RNF-03)
        factory = crear_factory({}, Gateway())
        self.assertIsInstance(factory._elegir_estrategia({'app_instalada': True}), AppStrategy)
        self.assertIsInstance(factory._elegir_estrategia({'telefono': '+56900000000'}), SmsStrategy)
        self.assertIsInstance(factory._elegir_estrategia({'email': 'paciente@ejemplo.cl'}), EmailStrategy)


class ListaEsperaTests(SimpleTestCase):
    def test_avisa_al_primero_de_la_fila(self):
        # RF-06 (Observer)
        gateway = Gateway()
        factory = crear_factory({'p2': {'id': 'p2', 'telefono': '+56900000000'}}, gateway)
        lista = ListaEspera(especialidad_id=1, notificacion_factory=factory)
        lista.agregar('p2')
        resultado = lista.notificar_siguiente(Hora(id_hora='h1', id_bloque=1, id_paciente='p1'))
        self.assertEqual(resultado, {'notificado': True, 'paciente_id': 'p2'})
        self.assertEqual(gateway.enviados[0][0], 'sms')
        self.assertIn('10 minutos', gateway.enviados[0][1]['texto'])

    def test_lista_vacia_no_notifica(self):
        lista = ListaEspera(especialidad_id=1, notificacion_factory=crear_factory({}, Gateway()))
        resultado = lista.notificar_siguiente(Hora(id_hora='h1', id_bloque=1, id_paciente='p1'))
        self.assertFalse(resultado['notificado'])
