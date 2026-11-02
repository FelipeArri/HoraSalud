"""
Patron Adapter (D26-C03) · B-18 · RF-01.

HoraSalud NO inscribe pacientes: consulta dos fuentes oficiales.
- Sistema clinico del CESFAM (tipo RAYEN): inscripcion, nombre y sector.
- FONASA (Certificador Previsional): prevision y tramo.

El resto del sistema conoce solo las interfaces SistemaClinicoService y
PrevisionService, con respuestas en un formato propio y estable. Cada adapter
traduce el formato de su sistema externo. Hoy los clientes externos son
simulados (sistemas_externos_simulados.py) con datos ficticios; con un
convenio real se cambia solo el cliente, no el resto del codigo.
"""


# ---------- Interfaces (lo que conoce HoraSalud) ----------

class SistemaClinicoService:
    def consultar_inscripcion(self, rut):
        """Devuelve {'inscrito', 'nombres', 'apellidos', 'sector', 'telefono'}."""
        raise NotImplementedError


class PrevisionService:
    # Previsiones posibles en el formato de HoraSalud
    FONASA, ISAPRE, DIPRECA, CAPREDENA, SIN_PREVISION = 'fonasa', 'isapre', 'dipreca', 'capredena', 'sin_prevision'

    def consultar_prevision(self, rut):
        """Devuelve {'prevision', 'tramo', 'vigente'}."""
        raise NotImplementedError


# ---------- Adapters (traducen cada sistema externo) ----------

class AdapterSistemaClinico(SistemaClinicoService):
    """Adapta la respuesta del sistema clinico (formato tipo RAYEN, simulado)."""

    def __init__(self, cliente_externo):
        self.cliente_externo = cliente_externo  # Adaptee

    def consultar_inscripcion(self, rut):
        ficha = self.cliente_externo.obtener(f'/pacientes/{rut}')
        if not ficha or ficha.get('estado_inscripcion') != 'ACTIVA':
            return {'inscrito': False, 'nombres': '', 'apellidos': '', 'sector': None, 'telefono': ''}
        apellidos = ' '.join(p for p in [ficha.get('apellido_paterno'), ficha.get('apellido_materno')] if p)
        sector = ficha.get('sector', '').strip().title()  # 'SECTOR 2' -> 'Sector 2'
        return {'inscrito': True, 'nombres': ficha.get('nombres', ''), 'apellidos': apellidos,
                'sector': sector or None, 'telefono': ficha.get('fono', '')}


class AdapterFonasa(PrevisionService):
    """Adapta la respuesta del certificador previsional (formato simulado)."""

    CODIGOS = {'FONASA': PrevisionService.FONASA, 'ISAPRE': PrevisionService.ISAPRE,
               'DIPRECA': PrevisionService.DIPRECA, 'CAPREDENA': PrevisionService.CAPREDENA}

    def __init__(self, cliente_externo):
        self.cliente_externo = cliente_externo  # Adaptee

    def consultar_prevision(self, rut):
        respuesta = self.cliente_externo.obtener(f'/certificador/{rut}')
        if not respuesta or not respuesta.get('afiliado_vigente'):
            return {'prevision': self.SIN_PREVISION, 'tramo': '', 'vigente': False}
        prevision = self.CODIGOS.get(respuesta.get('codigo_prevision'), self.SIN_PREVISION)
        tramo = respuesta.get('tramo', '') if prevision == self.FONASA else ''
        return {'prevision': prevision, 'tramo': tramo, 'vigente': True}


def servicios_externos():
    """Fabrica de los servicios usados por HoraSalud. Hoy: clientes simulados."""
    from .sistemas_externos_simulados import ClienteFonasaSimulado, ClienteSistemaClinicoSimulado
    return AdapterSistemaClinico(ClienteSistemaClinicoSimulado()), AdapterFonasa(ClienteFonasaSimulado())
