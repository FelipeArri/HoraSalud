"""
Patron Observer (D26-C03).

ListaEspera actua como Subject: ante un No-Show o una cancelacion avisa
al siguiente paciente en espera, sin que la Hora conozca la logica de
notificacion (bajo acoplamiento).
"""
from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema


class ListaEspera:
    def __init__(self, especialidad_id, notificacion_factory):
        self.especialidad_id = especialidad_id
        self.pacientes_en_espera = []  # orden FIFO
        self.notificacion_factory = notificacion_factory
        self.configuracion = ConfiguracionSistema()

    def agregar(self, paciente_id):
        self.pacientes_en_espera.append(paciente_id)

    def notificar_siguiente(self, hora):
        # RF-06
        if not self.pacientes_en_espera:
            return {'notificado': False, 'motivo': 'Lista de espera vacia'}
        paciente_id = self.pacientes_en_espera.pop(0)
        plazo = self.configuracion.plazo_confirmacion_reasignacion_min
        notificacion = self.notificacion_factory.crear_notificacion(
            paciente_id=paciente_id,
            hora_id=hora.id_hora,
            mensaje=f'Cupo liberado. Confirma en {plazo} minutos.',
        )
        notificacion.enviar()
        return {'notificado': True, 'paciente_id': paciente_id}
