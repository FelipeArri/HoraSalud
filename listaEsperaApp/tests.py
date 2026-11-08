from django.test import SimpleTestCase

from agendaApp.estados_hora import Hora
from notificacionesApp.estrategias import AvisoEnAppStrategy, PushStrategy
from notificacionesApp.notificacion_factory import NotificacionFactory

from .lista_espera import ListaEspera


class ServicioPush:
    def __init__(self):
        self.enviados = []

    def enviar(self, **datos):
        self.enviados.append(('push', datos))
        return True


class RepositorioUsuarios:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def buscar_por_id(self, usuario_id):
        return self.usuarios[usuario_id]


def crear_factory(usuarios, push):
    return NotificacionFactory(RepositorioUsuarios(usuarios), push)


class NotificacionFactoryTests(SimpleTestCase):
    def test_elige_el_canal_segun_los_datos_del_paciente(self):
        # Factory Method + Strategy (RNF-03): ambos canales son gratuitos
        factory = crear_factory({}, ServicioPush())
        self.assertIsInstance(factory._elegir_estrategia({'app_instalada': True}), PushStrategy)
        self.assertIsInstance(factory._elegir_estrategia({'app_instalada': False}), AvisoEnAppStrategy)


class ListaEsperaTests(SimpleTestCase):
    def test_avisa_al_primero_de_la_fila(self):
        # RF-06 (Observer)
        push = ServicioPush()
        factory = crear_factory({'p2': {'id': 'p2', 'app_instalada': True}}, push)
        lista = ListaEspera(especialidad_id=1, notificacion_factory=factory)
        lista.agregar('p2')
        resultado = lista.notificar_siguiente(Hora(id_hora='h1', id_bloque=1, id_paciente='p1'))
        self.assertEqual(resultado, {'notificado': True, 'paciente_id': 'p2'})
        self.assertEqual(push.enviados[0][0], 'push')
        self.assertIn('10 minutos', push.enviados[0][1]['texto'])

    def test_lista_vacia_no_notifica(self):
        lista = ListaEspera(especialidad_id=1, notificacion_factory=crear_factory({}, ServicioPush()))
        resultado = lista.notificar_siguiente(Hora(id_hora='h1', id_bloque=1, id_paciente='p1'))
        self.assertFalse(resultado['notificado'])
