"""
Patron Strategy (D26-C03): una interfaz comun para cada canal de aviso.

Los dos canales son GRATUITOS (costo cero para el CESFAM):
- PushStrategy: aviso push al telefono (suena y vibra aunque la app este cerrada).
- AvisoEnAppStrategy: el aviso queda visible dentro de HoraSalud (al entrar, el
  paciente ve "Se libero una hora para ti"). Siempre funciona: es el respaldo.
No se usan SMS ni correo: tendrian un costo por mensaje o un servicio externo.
"""


class CanalEnvio:
    def enviar(self, mensaje, destinatario):
        raise NotImplementedError


class PushStrategy(CanalEnvio):
    def __init__(self, servicio_push):
        self.servicio_push = servicio_push

    def enviar(self, mensaje, destinatario):
        return self.servicio_push.enviar(usuario_id=destinatario['id'], texto=mensaje)


class AvisoEnAppStrategy(CanalEnvio):
    def enviar(self, mensaje, destinatario):
        # No sale del sistema: el aviso se muestra en el inicio del paciente (y de su tutor)
        return True
