"""
Reglas de negocio del agendamiento (RF-02, RF-05, RN-01 a RN-05).

Las vistas (pantallas) solo llaman a estas funciones: asi las reglas estan
en un solo lugar y se pueden probar sin navegador.
"""
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema

from .estados_hora import TransicionInvalida
from .models import BloqueHorario, Hora

ESTADOS_VIGENTES = [Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA]

MOTIVOS_CANCELACION = [
    'No puedo asistir ese día',
    'Ya me siento mejor',
    'Prefiero otro horario',
    'Otro motivo',
]


class ReglaNegocioError(Exception):
    """Mensaje pensado para mostrarse tal cual al usuario."""


def inicio_bloque(bloque):
    return timezone.make_aware(datetime.combine(bloque.agenda.fecha, bloque.hora_inicio))


def _limite_reserva():
    # RN-03: horizonte maximo de reserva
    return timezone.localdate() + timedelta(days=ConfiguracionSistema().horizonte_maximo_reserva_dias)


def bloques_reservables(especialidad):
    """Bloques libres, futuros y dentro del horizonte de reserva."""
    ahora = timezone.localtime()
    bloques = (BloqueHorario.objects
               .filter(estado=BloqueHorario.Estado.DISPONIBLE, agenda__especialidad=especialidad,
                       agenda__fecha__gte=ahora.date(), agenda__fecha__lte=_limite_reserva())
               .select_related('agenda__profesional__usuario', 'agenda__especialidad'))
    return [b for b in bloques if inicio_bloque(b) > ahora]


def horas_vigentes(paciente):
    hoy = timezone.localdate()
    return (Hora.objects.filter(paciente=paciente, estado__in=ESTADOS_VIGENTES, bloque__agenda__fecha__gte=hoy)
            .select_related('bloque__agenda__especialidad', 'bloque__agenda__profesional__usuario'))


def reservar_hora(paciente, bloque_id):
    """RF-02. Devuelve la Hora creada o lanza ReglaNegocioError."""
    from . import prevision  # B-19: se importa aqui para evitar una importacion circular
    prevision.revalidar(paciente)  # consulta FONASA si la ultima consulta tiene mas de 30 dias
    if paciente.estado_inscripcion != paciente.Estado.VIGENTE:
        raise ReglaNegocioError(prevision.mensaje_no_vigente(paciente))  # RN-16
    with transaction.atomic():
        # select_for_update: si dos personas confirman a la vez, la segunda espera y luego ve el bloque tomado
        bloque = (BloqueHorario.objects.select_for_update()
                  .select_related('agenda__especialidad').get(pk=bloque_id))
        if bloque.estado != BloqueHorario.Estado.DISPONIBLE:
            raise ReglaNegocioError('Ese horario acaba de ser tomado por otra persona. Elige otro, por favor.')
        if inicio_bloque(bloque) <= timezone.localtime():
            raise ReglaNegocioError('Ese horario ya pasó. Elige otro, por favor.')
        if bloque.agenda.fecha > _limite_reserva():
            raise ReglaNegocioError('Solo se puede reservar dentro de los próximos '
                                    f'{ConfiguracionSistema().horizonte_maximo_reserva_dias} días.')  # RN-03
        especialidad = bloque.agenda.especialidad
        if horas_vigentes(paciente).filter(bloque__agenda__especialidad=especialidad).exists():
            raise ReglaNegocioError(f'Ya tienes una hora vigente en {especialidad}. '
                                    'Si necesitas otra, primero cancela la que tienes.')  # RN-01
        try:
            with transaction.atomic():
                return Hora.objects.create(bloque=bloque, paciente=paciente)
        except IntegrityError:  # RN-02: la base de datos impide la doble reserva
            raise ReglaNegocioError('Ese horario acaba de ser tomado por otra persona. Elige otro, por favor.')


def cancelar_hora(hora, motivo, quien='Paciente'):
    """RN-04 (plazo minimo) y RN-05 (motivo obligatorio)."""
    if hora.estado not in ESTADOS_VIGENTES:
        raise ReglaNegocioError('Esta hora ya no se puede cancelar.')
    if not motivo or not motivo.strip():
        raise ReglaNegocioError('Elige el motivo de la cancelación.')
    horas_minimas = ConfiguracionSistema().cancelacion_minima_horas
    if inicio_bloque(hora.bloque) - timezone.localtime() < timedelta(hours=horas_minimas):
        raise ReglaNegocioError(f'Solo puedes cancelar hasta {horas_minimas} horas antes. '
                                'Llama o acércate al SOME del CESFAM.')
    hora.estado = Hora.Estado.CANCELADA
    hora.motivo_cancelacion = f'{quien}: {motivo.strip()}'[:200]
    hora.save()
    return hora


# --- Acciones del SOME (RF-05) ---

def confirmar_asistencia(hora):
    """El paciente avisa que si asistira (D12: Reservada -> Confirmada)."""
    if hora.estado != Hora.Estado.RESERVADA:
        raise ReglaNegocioError('Esta hora ya estaba confirmada.')
    hora.estado = Hora.Estado.CONFIRMADA
    hora.save()


def marcar_atendida(hora):
    if hora.estado not in ESTADOS_VIGENTES:
        raise TransicionInvalida('Esta hora ya fue cerrada.')
    hora.estado = Hora.Estado.ATENDIDA
    hora.save()


def puede_marcar_no_show(hora):
    tolerancia = timedelta(minutes=ConfiguracionSistema().tolerancia_no_show_minutos)
    return hora.estado in ESTADOS_VIGENTES and timezone.localtime() >= inicio_bloque(hora.bloque) + tolerancia


def marcar_no_show(hora):
    """RF-05: inasistencia solo despues de la tolerancia (20 min)."""
    if not puede_marcar_no_show(hora):
        raise TransicionInvalida('Aún no se cumple la tolerancia de '
                                 f'{ConfiguracionSistema().tolerancia_no_show_minutos} minutos.')
    hora.estado = Hora.Estado.NO_SHOW
    hora.save()
