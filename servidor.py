"""
B-16 · Inicia HoraSalud en MODO PRODUCCIÓN (para la demostración o el piloto).

Uso (con el entorno virtual activo y DJANGO_DEBUG=False en .env):
    python servidor.py              -> http://127.0.0.1:8000 (para el túnel HTTPS)
    python servidor.py --puerto 8080

Qué hace:
1. Revisa la configuración de seguridad de Django (check --deploy).
2. Prepara los estilos, scripts e imágenes (collectstatic).
3. Deja corriendo las tareas automáticas cada 60 s (lista de espera y recordatorios).
4. Atiende con waitress, un servidor web gratuito apto para producción en Windows.

No aplica migraciones solo: eso se hace a mano (python manage.py migrate) para no
cambiar la base de datos sin que alguien lo decida.
"""
import argparse
import logging
import os
import threading
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoHoraSalud.settings')

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from waitress import serve  # noqa: E402

from proyectoHoraSalud.tareas import ejecutar  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('horasalud')


def tareas_cada(segundos):
    while True:
        try:
            ejecutar()
        except Exception:  # nunca se detiene: lo intenta de nuevo en el siguiente ciclo
            log.exception('Falló una revisión de tareas automáticas')
        time.sleep(segundos)


def main():
    parser = argparse.ArgumentParser(description='HoraSalud en modo producción')
    parser.add_argument('--puerto', type=int, default=8000)
    args = parser.parse_args()

    if settings.DEBUG:
        raise SystemExit('DJANGO_DEBUG está en True. Para producción pon DJANGO_DEBUG=False en .env.')
    call_command('check', deploy=True)
    call_command('collectstatic', interactive=False, verbosity=0)
    log.info('Archivos estáticos listos en %s', settings.STATIC_ROOT)
    # Se carga DESPUÉS de collectstatic: whitenoise revisa la carpeta de estáticos al iniciar
    from proyectoHoraSalud.wsgi import application

    threading.Thread(target=tareas_cada, args=(60,), daemon=True, name='tareas').start()
    log.info('Tareas automáticas: cada 60 segundos (lista de espera y recordatorios)')

    log.info('HoraSalud atendiendo en http://127.0.0.1:%s (ciérralo con Ctrl+C)', args.puerto)
    # Solo escucha en este equipo: desde afuera se entra por el túnel HTTPS, que llega desde 127.0.0.1.
    # El túnel avisa con X-Forwarded-Proto/Host que la conexión original era HTTPS y con qué dominio.
    # connection_limit: por defecto waitress acepta 100 conexiones simultáneas; con 150 usuarios (RNF-01)
    # las demás esperaban hasta 30 s (hallazgo de CP-37, EJE-03). Se sube a 300.
    serve(application, host='127.0.0.1', port=args.puerto, threads=8, connection_limit=300,
          trusted_proxy='127.0.0.1', trusted_proxy_count=1,
          trusted_proxy_headers={'x-forwarded-proto', 'x-forwarded-host', 'x-forwarded-for'},
          clear_untrusted_proxy_headers=True)


if __name__ == '__main__':
    main()
