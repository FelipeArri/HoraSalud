"""
B-23 · Recordatorio de la hora el día anterior (RN-13, apoya RF-05: menos No-Show).

Cada hora vigente (reservada o confirmada) de MAÑANA recibe un solo aviso
gratuito: push al teléfono del paciente y de su tutor, o aviso dentro de
HoraSalud si no activó los avisos. Solo se envía de 08:00 a 20:00.

El texto no lleva datos de salud (Ley 19.628): ni especialidad ni profesional,
solo la hora. El detalle se ve al tocar el aviso, dentro de la app.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema

from .models import Hora
from .servicios import ESTADOS_VIGENTES

logger = logging.getLogger(__name__)


def en_horario(ahora):
    config, local = ConfiguracionSistema(), timezone.localtime(ahora)
    return config.avisos_desde_hora <= local.hour < config.avisos_hasta_hora


def mensaje_recordatorio(hora):
    texto = f'Recuerda: mañana tienes hora en el CESFAM a las {hora.bloque.hora_inicio:%H:%M}.'
    if hora.estado == Hora.Estado.RESERVADA:
        return texto + ' Confirma que irás o cancélala en HoraSalud.'
    return texto + ' Si no puedes ir, cancélala en HoraSalud.'


def horas_por_recordar(ahora):
    dia = timezone.localtime(ahora).date() + timedelta(days=ConfiguracionSistema().recordatorio_dias_antes)
    return (Hora.objects.filter(estado__in=ESTADOS_VIGENTES, bloque__agenda__fecha=dia,
                                recordatorio_enviado_en__isnull=True)
            .select_related('bloque', 'paciente__usuario', 'paciente__tutor'))


def enviar_recordatorios(ahora=None):
    """Envía los recordatorios pendientes. Devuelve cuántos se enviaron."""
    from notificacionesApp.envio import avisar
    ahora = ahora or timezone.now()
    if not en_horario(ahora):
        return 0
    enviados = 0
    for hora in horas_por_recordar(ahora):
        # Se marca ANTES de enviar y solo si nadie lo marcó: dos revisiones a la vez no duplican el aviso
        if not Hora.objects.filter(pk=hora.pk, recordatorio_enviado_en__isnull=True).update(
                recordatorio_enviado_en=ahora):
            continue
        try:
            avisar(hora.paciente, mensaje_recordatorio(hora), url=f'/mis-horas/{hora.pk}/', ttl=12 * 3600,
                   hora=hora)
            enviados += 1
        except Exception:  # un aviso que falla no detiene a los demás
            logger.exception('No se pudo enviar el recordatorio de la hora %s', hora.pk)
    return enviados


def recordatorio_de_manana(paciente, ahora=None):
    """La hora de mañana del paciente, para mostrar el aviso también dentro de la app."""
    ahora = ahora or timezone.now()
    dia = timezone.localtime(ahora).date() + timedelta(days=ConfiguracionSistema().recordatorio_dias_antes)
    return (Hora.objects.filter(paciente=paciente, estado__in=ESTADOS_VIGENTES, bloque__agenda__fecha=dia)
            .select_related('bloque').order_by('bloque__hora_inicio').first())
