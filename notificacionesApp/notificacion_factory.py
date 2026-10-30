"""
Patron Factory Method (D26-C03).

Elige el canal (Strategy) segun los datos del paciente: prefiere el canal
que efectivamente puede usar (RNF-03).
"""
import uuid

from .estrategias import AppStrategy, EmailStrategy, SmsStrategy


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
        self.estrategia.enviar(self.mensaje, self.destinatario)
        self.estado = 'enviada'


class NotificacionFactory:
    def __init__(self, repositorio_usuarios, gateway_sms, gateway_email, servicio_push):
        self.repositorio_usuarios = repositorio_usuarios
        self.gateway_sms = gateway_sms
        self.gateway_email = gateway_email
        self.servicio_push = servicio_push

    def crear_notificacion(self, paciente_id, hora_id, mensaje):
        destinatario = self.repositorio_usuarios.buscar_por_id(paciente_id)
        return Notificacion(hora_id, destinatario, mensaje, self._elegir_estrategia(destinatario))

    def _elegir_estrategia(self, destinatario):
        if destinatario.get('app_instalada'):
            return AppStrategy(self.servicio_push)
        if destinatario.get('telefono'):
            return SmsStrategy(self.gateway_sms)
        return EmailStrategy(self.gateway_email)
