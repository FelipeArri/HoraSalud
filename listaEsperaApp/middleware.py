"""
B-14 y B-23 · Ejecuta las tareas automáticas sin necesidad de un programa aparte.

Con cada visita (como máximo una vez cada 30 segundos) vence las ofertas de la
lista de espera y envía los recordatorios de mañana (proyectoHoraSalud.tareas).
En un servidor real se deja además corriendo "python manage.py tareas_horasalud --cada 60".
"""
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
CLAVE = 'horasalud:lista_espera_revisada'


class ProcesarListaEsperaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (getattr(settings, 'HORASALUD_LISTA_ESPERA_AUTOMATICA', False)
                and not request.path.startswith(('/static/', '/sw.js', '/manifest', '/favicon'))
                and cache.add(CLAVE, 1, 30)):
            try:
                from proyectoHoraSalud.tareas import ejecutar
                ejecutar()
            except Exception:  # nunca debe impedir que la página cargue
                logger.exception('No se pudieron ejecutar las tareas automáticas')
        return self.get_response(request)
