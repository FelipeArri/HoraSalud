"""
Tareas automáticas de HoraSalud (B-14 y B-23), en un solo lugar:
- lista de espera: vencer ofertas sin respuesta y avisar al siguiente;
- recordatorios: avisar el día anterior a quienes tienen hora mañana.

Las ejecuta el middleware con las visitas (cada 30 s como máximo) y, en el
servidor real, el comando:  python manage.py tareas_horasalud --cada 60
"""
import logging

logger = logging.getLogger(__name__)


def ejecutar():
    from agendaApp.recordatorios import enviar_recordatorios
    from listaEsperaApp.servicios import procesar

    resultado = {}
    for nombre, tarea in (('lista_espera', procesar), ('recordatorios', enviar_recordatorios)):
        try:  # si una tarea falla, la otra igual se ejecuta
            resultado[nombre] = tarea()
        except Exception:
            logger.exception('Falló la tarea automática %s', nombre)
            resultado[nombre] = None
    return resultado
