"""
Patron Factory Method (D26-C03).

Elige el canal (Strategy) segun los datos del paciente: si activo los avisos en
su telefono (o en el de su tutor), aviso push; si no, aviso dentro de la app
(RNF-03). Ambos canales son gratuitos.
"""
import uuid

from .estrategias import AvisoEnAppStrategy, PushStrategy


class Notificacion:
    def __init__(self, hora_id, destinatario, mensaje, estrategia):
        self.id = str(uuid.uuid4())
        self.hora_id = hora_id
        self.destinatario = destinatario
        self.mensaje = mensaje
        self.estado = 'pendiente'
        self.estrategia = estrategia

    def enviar(self):
        # La notificacion no sabe COMO se envia: delega en la Strategy
        resultado = self.estrategia.enviar(self.mensaje, self.destinatario)
        self.estado = 'enviada' if resultado else 'fallida'
        return resultado


class NotificacionFactory:
    def __init__(self, repositorio_usuarios, servicio_push):
        self.repositorio_usuarios = repositorio_usuarios
        self.servicio_push = servicio_push

    def crear_notificacion(self, paciente_id, hora_id, mensaje):
        destinatario = self.repositorio_usuarios.buscar_por_id(paciente_id)
        return Notificacion(hora_id, destinatario, mensaje, self._elegir_estrategia(destinatario))

    def _elegir_estrategia(self, destinatario):
        if destinatario.get('app_instalada'):
            return PushStrategy(self.servicio_push)
        return AvisoEnAppStrategy()
