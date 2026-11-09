"""
B-14 · HoraSalud como aplicación instalable (PWA) y avisos push gratuitos.

- /manifest.webmanifest: nombre, ícono y colores con que se instala en el teléfono.
- /sw.js: el "service worker", el pequeño programa que recibe los avisos aunque
  la app esté cerrada. Debe servirse desde la raíz para cubrir todo el sitio.
- /avisos/suscribir/: guarda el dispositivo que aceptó recibir avisos.
- /avisos/prueba/: envía un aviso de prueba al propio usuario.
"""
import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST

from .envio import enviar_push, push_configurado
from .models import SuscripcionPush

# OWASP A10 (SSRF): el servidor solo envía avisos a los servicios oficiales de los navegadores.
SERVICIOS_PUSH = ('fcm.googleapis.com', 'android.googleapis.com', 'push.services.mozilla.com',
                  'push.apple.com', 'notify.windows.com')


def endpoint_permitido(endpoint):
    partes = urlparse(endpoint or '')
    host = (partes.hostname or '').lower()
    return (partes.scheme == 'https' and len(endpoint) <= 700
            and any(host == s or host.endswith('.' + s) for s in SERVICIOS_PUSH))


@cache_control(max_age=3600)
def manifest(request):
    datos = {
        'id': '/',
        'name': 'HoraSalud · CESFAM Padre Esteban Gumucio',
        'short_name': 'HoraSalud',
        'description': 'Pide, confirma y cancela tus horas del CESFAM.',
        'lang': 'es-CL',
        'start_url': '/mi-inicio/',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#f4f7f5',
        'theme_color': '#1f7a3a',
        'icons': [
            {'src': static('images/icono-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': static('images/icono-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': static('images/icono-maskable-192.png'), 'sizes': '192x192', 'type': 'image/png',
             'purpose': 'maskable'},
            {'src': static('images/icono-maskable-512.png'), 'sizes': '512x512', 'type': 'image/png',
             'purpose': 'maskable'},
        ],
    }
    return JsonResponse(datos, content_type='application/manifest+json', json_dumps_params={'ensure_ascii': False})


def service_worker(request):
    ruta = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    respuesta = HttpResponse(ruta.read_text(encoding='utf-8'), content_type='application/javascript')
    respuesta['Service-Worker-Allowed'] = '/'
    respuesta['Cache-Control'] = 'no-cache'  # así el teléfono recibe siempre la última versión
    return respuesta


def sin_conexion(request):
    return render(request, 'notificacionesApp/sin_conexion.html')


@require_POST
@login_required(login_url='ingresar')
def suscribir(request):
    try:
        datos = json.loads(request.body or b'{}')
        endpoint, claves = datos.get('endpoint', ''), datos.get('keys') or {}
        p256dh, auth = str(claves.get('p256dh', ''))[:200], str(claves.get('auth', ''))[:100]
    except (ValueError, AttributeError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos.'}, status=400)
    if not endpoint_permitido(endpoint) or not p256dh or not auth:
        return JsonResponse({'ok': False, 'error': 'Este navegador no entregó un servicio de avisos válido.'},
                            status=400)
    SuscripcionPush.objects.update_or_create(endpoint=endpoint, defaults={
        'usuario': request.user, 'p256dh': p256dh, 'auth': auth,
        'navegador': request.META.get('HTTP_USER_AGENT', '')[:150]})
    return JsonResponse({'ok': True})


@require_POST
@login_required(login_url='ingresar')
def quitar(request):
    try:
        endpoint = json.loads(request.body or b'{}').get('endpoint', '')
    except ValueError:
        endpoint = ''
    SuscripcionPush.objects.filter(usuario=request.user, endpoint=endpoint).delete()
    return JsonResponse({'ok': True})


@require_POST
@login_required(login_url='ingresar')
def prueba(request):
    if not push_configurado():
        return JsonResponse({'ok': False, 'error': 'El servidor aún no tiene claves de avisos '
                                                   '(python manage.py generar_claves_push).'}, status=503)
    entregados = enviar_push(request.user, 'HoraSalud', 'Así te llegarán los avisos de HoraSalud. '
                             '¡Ya están activados!', '/mi-inicio/', ttl=300, etiqueta='prueba')
    return JsonResponse({'ok': entregados > 0, 'entregados': entregados})
