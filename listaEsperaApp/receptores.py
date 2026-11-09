"""
B-14 · Observer: la lista de espera escucha lo que pasa en la agenda.

- cupo_liberado (agendaApp.eventos): una hora se canceló -> se ofrece a la fila.
- post_save de Hora: el paciente consiguió hora en esa especialidad -> sale de la fila.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from agendaApp.eventos import cupo_liberado
from agendaApp.models import Hora

from . import servicios

logger = logging.getLogger(__name__)


@receiver(cupo_liberado, dispatch_uid='lista_espera_cupo_liberado')
def al_liberarse_un_cupo(sender, bloque, motivo='', **kwargs):
    try:
        servicios.registrar_cupo_liberado(bloque)
    except Exception:  # la cancelación del paciente nunca debe fallar por la lista de espera
        logger.exception('No se pudo ofrecer el cupo liberado a la lista de espera')


@receiver(post_save, sender=Hora, dispatch_uid='lista_espera_hora_tomada')
def al_tomar_una_hora(sender, instance, created, **kwargs):
    if created and instance.estado in (Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA):
        servicios.quitar_al_tener_hora(instance)
