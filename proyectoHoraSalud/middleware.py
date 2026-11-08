"""
DEF-03 (B-16): al cerrar sesion y presionar "atras", el navegador mostraba la
copia guardada de una pagina privada (por ejemplo, "Mi inicio" con la proxima
hora). La sesion ya estaba cerrada, pero los datos quedaban a la vista en un
telefono compartido (RN-12, Ley 20.584, Ley 21.719).

Solucion: las paginas de una sesion iniciada no se guardan en la memoria del
navegador (Cache-Control: no-store). Chrome y Safari tampoco las guardan en su
cache de "atras/adelante".
"""
import json

from django.http import HttpResponse


class SinCacheParaSesionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        usuario = getattr(request, 'user', None)
        if usuario is not None and usuario.is_authenticated:
            respuesta['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
            respuesta['Pragma'] = 'no-cache'
            respuesta['Expires'] = '0'
        return respuesta


# ---------------------------------------------------------------------------
# DEF-10 (CP-31, OWASP A06): Django 4.2 ya no recibe parches y DRF 3.18 (que
# corrige dos denegaciones de servicio) exige Django 5. Con MariaDB 10.4 de XAMPP
# no se puede usar Django 5, asi que este filtro mitiga esas dos fallas en la API
# hasta migrar a Django 5.2 (etapa final, con la base de AWS):
# - GHSA-33wh-fxxf-88vv: cabecera Accept enorme -> tiempo de proceso cuadratico.
# - GHSA-3547-9m27-7rxg: un "charset" de compresion en Content-Type salta el
#   limite de memoria del cuerpo.
# La API de HoraSalud solo habla JSON en UTF-8, asi que se rechaza lo demas.
# ---------------------------------------------------------------------------
LARGO_MAXIMO_ACCEPT = 256
CHARSETS_PERMITIDOS = {'', 'utf-8', 'utf8'}


def _respuesta_400(detalle):
    return HttpResponse(json.dumps({'detail': detalle}), status=400, content_type='application/json')


class CabecerasSegurasApiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            if len(request.META.get('HTTP_ACCEPT', '')) > LARGO_MAXIMO_ACCEPT:
                return _respuesta_400('Cabecera Accept demasiado larga.')
            tipo = request.META.get('CONTENT_TYPE', '')
            charset = ''
            for parte in tipo.split(';')[1:]:
                nombre, _, valor = parte.strip().partition('=')
                if nombre.strip().lower() == 'charset':
                    charset = valor.strip().strip('"').lower()
            if charset not in CHARSETS_PERMITIDOS:
                return _respuesta_400('Solo se acepta texto en UTF-8.')
        return self.get_response(request)
