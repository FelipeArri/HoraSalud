"""
Ciclo de vida de una Hora (D12-C03-Dia_Estados_Hora, D21-C03).

En el Sprint 5 estas reglas pasan al modelo Hora de models.py; por ahora
viven como clase de dominio para poder probarlas sin base de datos.
"""


class EstadoHora:
    RESERVADA = 'reservada'
    CONFIRMADA = 'confirmada'
    ATENDIDA = 'atendida'
    CANCELADA = 'cancelada'
    NO_SHOW = 'no_show'
    REASIGNADA = 'reasignada'


class TransicionInvalida(Exception):
    """La Hora no puede pasar al estado pedido desde su estado actual."""


class Hora:
    def __init__(self, id_hora, id_bloque, id_paciente):
        self.id_hora = id_hora
        self.id_bloque = id_bloque
        self.id_paciente = id_paciente
        self.estado = EstadoHora.RESERVADA
        self.motivo_cancelacion = None

    def confirmar(self):
        if self.estado != EstadoHora.RESERVADA:
            raise TransicionInvalida(f'No se puede confirmar una Hora en estado {self.estado}')
        self.estado = EstadoHora.CONFIRMADA

    def cancelar(self, motivo):
        # RN-05: toda cancelacion registra motivo
        if self.estado in (EstadoHora.ATENDIDA, EstadoHora.CANCELADA):
            raise TransicionInvalida(f'No se puede cancelar una Hora en estado {self.estado}')
        if not motivo or not motivo.strip():
            raise TransicionInvalida('La cancelacion requiere un motivo (RN-05)')
        self.estado = EstadoHora.CANCELADA
        self.motivo_cancelacion = motivo.strip()

    def marcar_no_show(self):
        # RF-05: solo una hora confirmada puede quedar como inasistencia
        if self.estado != EstadoHora.CONFIRMADA:
            raise TransicionInvalida(f'No se puede marcar No-Show desde el estado {self.estado}')
        self.estado = EstadoHora.NO_SHOW

    def reasignar(self, nuevo_paciente_id):
        # RF-06: se ejecuta cuando la lista de espera confirma a un nuevo paciente
        if self.estado not in (EstadoHora.NO_SHOW, EstadoHora.CANCELADA):
            raise TransicionInvalida(f'Solo se reasigna una Hora en No-Show o cancelada (estado: {self.estado})')
        self.id_paciente = nuevo_paciente_id
        self.estado = EstadoHora.REASIGNADA
