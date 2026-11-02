"""
Clientes que consultan la base fonasa_simulado y responden en el formato
"externo" que entienden los Adapter (como si fueran servicios web de FONASA).
Cambiar a un servicio real = cambiar solo estos clientes.
"""
from .models import CESFAM, PersonaFonasa


def _persona(ruta):
    return PersonaFonasa.objects.filter(rut=ruta.rsplit('/', 1)[-1]).first()


class ClienteFonasaBD:
    """Certificador previsional: previsión y tramo."""

    def obtener(self, ruta):
        p = _persona(ruta)
        if p is None:
            return None
        if p.prevision == PersonaFonasa.Prevision.SIN_PREVISION:
            return {'codigo_prevision': None, 'afiliado_vigente': False}
        return {'codigo_prevision': p.prevision, 'tramo': p.tramo, 'afiliado_vigente': True}


class ClienteInscripcionBD:
    """Inscripción per cápita: si está inscrita en ESTE CESFAM y en qué sector."""

    def obtener(self, ruta):
        p = _persona(ruta)
        if p is None or p.estado_inscripcion == PersonaFonasa.Inscripcion.NO_INSCRITO or p.establecimiento != CESFAM:
            return None
        return {'nombres': p.nombres, 'apellido_paterno': p.apellido_paterno, 'apellido_materno': p.apellido_materno,
                'establecimiento': p.establecimiento, 'sector': p.sector, 'estado_inscripcion': p.estado_inscripcion,
                'fono': p.telefono}
