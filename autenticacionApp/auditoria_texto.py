"""
RN-11 · Texto legible de cada registro de auditoría.

Arma una sola frase con quién actuó (rol, nombre y RUT), qué hizo, sobre quién
y el detalle. Ejemplo:
  "Administrativo SOME María Soto (11111111-1): Reservó una hora · para Paciente
   Raúl Carrasco (30000016-9). Medicina General · 07-11-2026 08:20"

Son funciones puras (sin modelos) para poder usarlas también en las migraciones.
"""
SISTEMA = 'Sistema HoraSalud'
LARGO_MAXIMO = 400


def persona(rol, nombre, rut):
    """'Paciente Raúl Carrasco (30000016-9)'; omite lo que falte."""
    texto = ' '.join(parte for parte in (rol, nombre) if parte)
    if rut:
        texto = f'{texto} ({rut})' if texto else rut
    return texto


def armar_descripcion(accion_texto, actor_rol='', actor_nombre='', actor_rut='',
                      objetivo_rol='', objetivo_nombre='', objetivo_rut='', detalle=''):
    quien = persona(actor_rol, actor_nombre, actor_rut) or SISTEMA
    frase = f'{quien}: {accion_texto}'
    if objetivo_rut and objetivo_rut != actor_rut:
        frase += f' · sobre {persona(objetivo_rol, objetivo_nombre, objetivo_rut)}'
    if detalle:
        frase += f'. {detalle}'
    return frase[:LARGO_MAXIMO]
