"""
Patron Adapter (D26-C03).

El sistema conoce solo la interfaz InscripcionService. El adapter traduce
la llamada al servicio externo de inscripcion (FONASA / municipalidad), de
modo que RF-01 no dependa de sus detalles. En el prototipo el servicio
externo se simula con datos ficticios.
"""


class InscripcionService:
    def consultar_inscripcion(self, rut):
        raise NotImplementedError('Usar una subclase, por ejemplo AdapterInscripcionFonasa')


class AdapterInscripcionFonasa(InscripcionService):
    MAPA_SECTORES = {
        'La Granja - Sector 1': 1,
        'La Granja - Sector 2': 2,
        'La Granja - Sector 3': 3,
    }

    def __init__(self, cliente_externo):
        self.cliente_externo = cliente_externo  # Adaptee

    def consultar_inscripcion(self, rut):
        # RF-01
        respuesta = self.cliente_externo.obtener(f'/fonasa/inscripcion/{rut}')
        if not respuesta or not respuesta.get('vigente'):
            return {'vigente': False, 'sector': None}
        return {'vigente': True, 'sector': self.MAPA_SECTORES.get(respuesta.get('comuna'))}
