"""
Sistemas externos SIMULADOS para el prototipo (B-18). SOLO DATOS FICTICIOS.

Imitan, con un formato propio, lo que responderian el sistema clinico del
CESFAM (tipo RAYEN) y el certificador previsional de FONASA. No son las APIs
reales: conectarse a ellas requiere convenio.

RUT de prueba (todos ficticios):
- 30.000.007-K a 30.000.018-5: pacientes demo de HoraSalud, inscritos con FONASA.
- 31.000.001-9: inscrita con FONASA B, aun NO esta en HoraSalud (persona nueva).
- 31.000.002-7: inscrito, ISAPRE.
- 31.000.003-5: inscrito, DIPRECA.
- 31.000.004-3: inscrito, CAPREDENA.
- 31.000.005-1: inscrita, sin prevision.
- 31.000.006-K: no inscrito en el CESFAM.
- 31.000.007-8: inscripcion pasiva (se cambio de CESFAM).
"""
from .validators import calcular_dv

# Nombres de los pacientes demo (mismo orden que cargar_datos_demo)
_DEMO = [('Rosa', 'Gonzalez', 'Mena'), ('Luis', 'Herrera', 'Diaz'), ('Carmen', 'Silva', 'Araya'),
         ('Pedro', 'Munoz', 'Tapia'), ('Elena', 'Contreras', 'Paz'), ('Manuel', 'Vargas', 'Reyes'),
         ('Teresa', 'Espinoza', 'Leiva'), ('Hector', 'Pizarro', 'Olivares'), ('Gloria', 'Saavedra', 'Nunez'),
         ('Raul', 'Carrasco', 'Bravo'), ('Ines', 'Sepulveda', 'Toro'), ('Oscar', 'Alarcon', 'Mella')]


def _rut(numero):
    return f'{numero}-{calcular_dv(str(numero))}'


def _ficha(nombres, paterno, materno, sector, estado='ACTIVA'):
    return {'nombres': nombres, 'apellido_paterno': paterno, 'apellido_materno': materno,
            'establecimiento': 'CESFAM Padre Esteban Gumucio', 'sector': f'SECTOR {sector}',
            'estado_inscripcion': estado, 'fono': ''}


FICHAS = {_rut(30000007 + i): _ficha(n, p, m, i % 3 + 1) for i, (n, p, m) in enumerate(_DEMO)}
FICHAS.update({
    _rut(31000001): _ficha('Ana María', 'Prueba', 'Ficticia', 2) | {'fono': '+56911112222'},
    _rut(31000002): _ficha('Bruno', 'Isapre', 'Ficticio', 1),
    _rut(31000003): _ficha('Carla', 'Dipreca', 'Ficticia', 3),
    _rut(31000004): _ficha('Daniel', 'Capredena', 'Ficticio', 2),
    _rut(31000005): _ficha('Eva', 'Sinprevision', 'Ficticia', 1),
    _rut(31000007): _ficha('Gabriel', 'Traslado', 'Ficticio', 2, estado='PASIVA'),
})

CERTIFICADOS = {_rut(30000007 + i): {'codigo_prevision': 'FONASA', 'tramo': 'ABCD'[i % 4], 'afiliado_vigente': True}
                for i in range(len(_DEMO))}
CERTIFICADOS.update({
    _rut(31000001): {'codigo_prevision': 'FONASA', 'tramo': 'B', 'afiliado_vigente': True},
    _rut(31000002): {'codigo_prevision': 'ISAPRE', 'afiliado_vigente': True},
    _rut(31000003): {'codigo_prevision': 'DIPRECA', 'afiliado_vigente': True},
    _rut(31000004): {'codigo_prevision': 'CAPREDENA', 'afiliado_vigente': True},
    _rut(31000005): {'codigo_prevision': None, 'afiliado_vigente': False},
    _rut(31000006): {'codigo_prevision': 'FONASA', 'tramo': 'A', 'afiliado_vigente': True},
    _rut(31000007): {'codigo_prevision': 'FONASA', 'tramo': 'C', 'afiliado_vigente': True},
})


class ClienteSistemaClinicoSimulado:
    """Hace las veces del sistema clinico del CESFAM (tipo RAYEN)."""

    def obtener(self, ruta):
        return FICHAS.get(ruta.rsplit('/', 1)[-1])


class ClienteFonasaSimulado:
    """Hace las veces del certificador previsional de FONASA."""

    def obtener(self, ruta):
        return CERTIFICADOS.get(ruta.rsplit('/', 1)[-1])
