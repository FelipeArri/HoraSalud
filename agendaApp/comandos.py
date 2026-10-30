"""
Patron Command (D26-C03).

Cada accion sobre una Hora es un comando ejecutable y auditable (RN-11).
Los repositorios se inyectan; en el Sprint 5 se reemplazan por los modelos
de Django.
"""
from datetime import datetime


class Comando:
    def ejecutar(self):
        raise NotImplementedError


class ReservarHoraCommand(Comando):
    def __init__(self, repositorio_bloques, repositorio_horas, registro_auditoria, bloque_id, paciente_id):
        self.repositorio_bloques = repositorio_bloques
        self.repositorio_horas = repositorio_horas
        self.registro_auditoria = registro_auditoria
        self.bloque_id = bloque_id
        self.paciente_id = paciente_id

    def ejecutar(self):
        # RF-02, RN-02
        bloque = self.repositorio_bloques.buscar_por_id(self.bloque_id)
        if bloque is None or bloque.estado != 'disponible':
            raise ValueError('El bloque horario no esta disponible (RN-02)')
        hora = self.repositorio_horas.crear(id_bloque=self.bloque_id, id_paciente=self.paciente_id)
        bloque.estado = 'reservado'
        self.registro_auditoria.registrar(accion='ReservarHora', id_hora=hora.id_hora,
                                          id_usuario=self.paciente_id, fecha=datetime.now())
        return hora


class MarcarNoShowCommand(Comando):
    def __init__(self, repositorio_horas, registro_auditoria, lista_espera, hora_id, usuario_id):
        self.repositorio_horas = repositorio_horas
        self.registro_auditoria = registro_auditoria
        self.lista_espera = lista_espera  # Subject del patron Observer
        self.hora_id = hora_id
        self.usuario_id = usuario_id

    def ejecutar(self):
        # RF-05; dispara RF-06 a traves de la lista de espera
        hora = self.repositorio_horas.buscar_por_id(self.hora_id)
        hora.marcar_no_show()
        self.registro_auditoria.registrar(accion='MarcarNoShow', id_hora=hora.id_hora,
                                          id_usuario=self.usuario_id, fecha=datetime.now())
        if self.lista_espera is not None:
            self.lista_espera.notificar_siguiente(hora)
        return hora
