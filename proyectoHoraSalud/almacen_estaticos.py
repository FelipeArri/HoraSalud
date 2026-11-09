"""
B-16 · Archivos estáticos en producción (whitenoise).

Igual que CompressedManifestStaticFilesStorage, pero sin seguir las líneas
"sourceMappingURL" (mapas de depuración de Bootstrap que no se incluyen en el
proyecto). Así no hay que modificar los archivos originales de Bootstrap.
"""
from whitenoise.storage import CompressedManifestStaticFilesStorage


def _sin_mapas(patrones):
    resultado = []
    for extension, reglas in patrones:
        reglas = tuple(r for r in reglas if 'sourceMappingURL' not in (r if isinstance(r, str) else r[0]))
        if reglas:
            resultado.append((extension, reglas))
    return tuple(resultado)


class AlmacenEstaticos(CompressedManifestStaticFilesStorage):
    patterns = _sin_mapas(CompressedManifestStaticFilesStorage.patterns)
