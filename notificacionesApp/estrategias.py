"""
Patron Strategy (D26-C03): una interfaz comun para cada canal de envio.
"""


class CanalEnvio:
    def enviar(self, mensaje, destinatario):
        raise NotImplementedError


class SmsStrategy(CanalEnvio):
    def __init__(self, gateway_sms):
        self.gateway_sms = gateway_sms

    def enviar(self, mensaje, destinatario):
        return self.gateway_sms.enviar_sms(telefono=destinatario['telefono'], texto=mensaje)


class EmailStrategy(CanalEnvio):
    def __init__(self, gateway_email):
        self.gateway_email = gateway_email

    def enviar(self, mensaje, destinatario):
        return self.gateway_email.enviar_correo(para=destinatario['email'], cuerpo=mensaje)


class AppStrategy(CanalEnvio):
    def __init__(self, servicio_push):
        self.servicio_push = servicio_push

    def enviar(self, mensaje, destinatario):
        return self.servicio_push.enviar(usuario_id=destinatario['id'], texto=mensaje)
