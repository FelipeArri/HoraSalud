"""
DEF-08 · Límite de intentos en el ingreso de pacientes y tutores (OWASP A04 y A07).

- Por origen (IP): 10 RUT no encontrados en 15 minutos bloquean ese origen 15 minutos,
  en el ingreso y en el enrolamiento. Así no se puede probar RUT tras RUT.
- Por RUT: 5 huellas (passkeys) rechazadas en 15 minutos bloquean el ingreso de ese
  RUT 15 minutos. Queda en el registro de auditoría.

Los contadores viven en la caché de Django. Con la caché por defecto (memoria del
proceso) basta para el prototipo; al publicar con varios procesos conviene una caché
compartida (base de datos o Redis) en settings.CACHES.
"""
from django.core.cache import cache

from .models import RegistroAuditoria
from .personal import _ip, auditar

VENTANA_SEGUNDOS = 15 * 60
MINUTOS_BLOQUEO = VENTANA_SEGUNDOS // 60
MAX_RUT_POR_ORIGEN = 10
MAX_HUELLAS_POR_RUT = 5

AVISO_ORIGEN = (f'Hiciste demasiados intentos. Espera {MINUTOS_BLOQUEO} minutos o acércate '
                'al SOME del CESFAM.')
AVISO_RUT = (f'Por seguridad, el ingreso con este RUT quedó bloqueado {MINUTOS_BLOQUEO} minutos. '
             'Si no eres tú quien lo intentó, avisa en el SOME del CESFAM.')


def _clave(tipo, valor):
    return f'limite_intentos:{tipo}:{valor}'


def _contar(clave):
    """Suma un intento fallido. La ventana parte con el primer fallo y no se alarga."""
    if cache.add(clave, 1, VENTANA_SEGUNDOS):
        return 1
    try:
        return cache.incr(clave)
    except ValueError:  # venció justo entre add() e incr()
        cache.set(clave, 1, VENTANA_SEGUNDOS)
        return 1


def _origen(request):
    return _ip(request) or 'desconocido'


# ---------- Por origen (RUT no encontrado) ----------

def origen_bloqueado(request):
    return cache.get(_clave('origen', _origen(request)), 0) >= MAX_RUT_POR_ORIGEN


def registrar_rut_no_encontrado(request):
    _contar(_clave('origen', _origen(request)))


# ---------- Por RUT (huella rechazada) ----------

def rut_bloqueado(usuario):
    return cache.get(_clave('rut', usuario.pk), 0) >= MAX_HUELLAS_POR_RUT


def registrar_huella_rechazada(request, usuario):
    """Devuelve True si con este fallo el RUT quedó bloqueado."""
    intentos = _contar(_clave('rut', usuario.pk))
    if intentos == MAX_HUELLAS_POR_RUT:
        auditar(request, RegistroAuditoria.Accion.INGRESO_BLOQUEADO, actor=usuario, objetivo=usuario,
                detalle=f'{MAX_HUELLAS_POR_RUT} huellas rechazadas: bloqueo de {MINUTOS_BLOQUEO} min')
    return intentos >= MAX_HUELLAS_POR_RUT


def ingreso_correcto(usuario):
    cache.delete(_clave('rut', usuario.pk))
