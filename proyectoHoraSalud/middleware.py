"""
DEF-03 (B-16): al cerrar sesion y presionar "atras", el navegador mostraba la
copia guardada de una pagina privada (por ejemplo, "Mi inicio" con la proxima
hora). La sesion ya estaba cerrada, pero los datos quedaban a la vista en un
telefono compartido (RN-12, Ley 20.584, Ley 21.719).

Solucion: las paginas de una sesion iniciada no se guardan en la memoria del
navegador (Cache-Control: no-store). Chrome y Safari tampoco las guardan en su
cache de "atras/adelante".
"""


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
