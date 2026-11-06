"""
Reglas de negocio del agendamiento (RF-02, RF-05, RN-01 a RN-05).

Las vistas (pantallas) solo llaman a estas funciones: asi las reglas estan
en un solo lugar y se pueden probar sin navegador.
"""
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from autenticacionApp.models import RegistroAuditoria
from autenticacionApp.personal import auditar
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


def filtro_sector(paciente):
    """DEF-06 (RF-02): el paciente ve las agendas de su sector y las de los profesionales
    sin sector, que atienden a todos (por ejemplo, los programas)."""
    if paciente is None:  # uso interno (SOME, pruebas): sin filtro
        return Q()
    todos_los_sectores = Q(agenda__profesional__sector__isnull=True)
    if paciente.sector_id is None:
        return todos_los_sectores
    return todos_los_sectores | Q(agenda__profesional__sector_id=paciente.sector_id)


def _detalle_hora(hora):
    # Sin el motivo ni datos clínicos: solo qué hora se tocó
    bloque = hora.bloque
    return f'{bloque.agenda.especialidad} · {bloque.agenda.fecha:%d-%m-%Y} {bloque.hora_inicio:%H:%M}'


def bloques_reservables(especialidad, paciente=None):
    """Bloques libres, futuros, dentro del horizonte de reserva y del sector del paciente."""
    ahora = timezone.localtime()
    bloques = (BloqueHorario.objects
               .filter(filtro_sector(paciente))
               .filter(estado=BloqueHorario.Estado.DISPONIBLE, agenda__especialidad=especialidad,
                       agenda__fecha__gte=ahora.date(), agenda__fecha__lte=_limite_reserva(),
                       tipo_cupo=BloqueHorario.TipoCupo.PROGRAMADO)  # B-21: ventanilla no se ve en la app
               .select_related('agenda__profesional__usuario', 'agenda__especialidad'))
    return [b for b in bloques if inicio_bloque(b) > ahora]


def horas_vigentes(paciente):
    hoy = timezone.localdate()
    return (Hora.objects.filter(paciente=paciente, estado__in=ESTADOS_VIGENTES, bloque__agenda__fecha__gte=hoy)
            .select_related('bloque__agenda__especialidad', 'bloque__agenda__profesional__usuario'))


def reservar_hora(paciente, bloque_id, request=None):
    """RF-02. Devuelve la Hora creada o lanza ReglaNegocioError."""
    from . import prevision  # B-19: se importa aqui para evitar una importacion circular
    prevision.revalidar(paciente)  # consulta FONASA si la ultima consulta tiene mas de 30 dias
    if paciente.estado_inscripcion != paciente.Estado.VIGENTE:
        raise ReglaNegocioError(prevision.mensaje_no_vigente(paciente))  # RN-16
    with transaction.atomic():
        # select_for_update: si dos personas confirman a la vez, la segunda espera y luego ve el bloque tomado
        bloque = (BloqueHorario.objects.select_for_update()
                  .select_related('agenda__especialidad').get(pk=bloque_id))
        if bloque.tipo_cupo != BloqueHorario.TipoCupo.PROGRAMADO:
            raise ReglaNegocioError('Ese horario se entrega solo en el SOME del CESFAM.')  # B-21
        if not BloqueHorario.objects.filter(pk=bloque.pk).filter(filtro_sector(paciente)).exists():
            raise ReglaNegocioError('Ese horario es de otro sector del CESFAM. '
                                    'Elige uno de tu sector, por favor.')  # DEF-06
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
                hora = Hora.objects.create(bloque=bloque, paciente=paciente)
        except IntegrityError:  # RN-02: la base de datos impide la doble reserva
            raise ReglaNegocioError('Ese horario acaba de ser tomado por otra persona. Elige otro, por favor.')
    from .gestion_agendas import resolver_indicacion_al_reservar
    resolver_indicacion_al_reservar(hora)  # P-10: ya pidió su control
    auditar(request, RegistroAuditoria.Accion.RESERVA, objetivo=paciente.usuario,
            detalle=_detalle_hora(hora))  # DEF-07 (RN-11)
    return hora


def cancelar_hora(hora, motivo, quien='Paciente', request=None):
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
    auditar(request, RegistroAuditoria.Accion.CANCELACION, objetivo=hora.paciente.usuario,
            detalle=f'{quien} · {_detalle_hora(hora)}')  # DEF-07 (RN-11); el motivo va cifrado, no se copia
    return hora


# --- Acciones del SOME (RF-05) ---

def confirmar_asistencia(hora):
    """El paciente avisa que si asistira (D12: Reservada -> Confirmada)."""
    if hora.estado != Hora.Estado.RESERVADA:
        raise ReglaNegocioError('Esta hora ya estaba confirmada.')
    hora.estado = Hora.Estado.CONFIRMADA
    hora.save()


def marcar_atendida(hora, request=None):
    if hora.estado not in ESTADOS_VIGENTES:
        raise TransicionInvalida('Esta hora ya fue cerrada.')
    hora.estado = Hora.Estado.ATENDIDA
    hora.save()
    auditar(request, RegistroAuditoria.Accion.ATENDIDA, objetivo=hora.paciente.usuario,
            detalle=_detalle_hora(hora))


def puede_marcar_no_show(hora):
    tolerancia = timedelta(minutes=ConfiguracionSistema().tolerancia_no_show_minutos)
    return hora.estado in ESTADOS_VIGENTES and timezone.localtime() >= inicio_bloque(hora.bloque) + tolerancia


def marcar_no_show(hora, request=None):
    """RF-05: inasistencia solo despues de la tolerancia (20 min)."""
    if not puede_marcar_no_show(hora):
        raise TransicionInvalida('Aún no se cumple la tolerancia de '
                                 f'{ConfiguracionSistema().tolerancia_no_show_minutos} minutos.')
    hora.estado = Hora.Estado.NO_SHOW
    hora.save()
    auditar(request, RegistroAuditoria.Accion.NO_SHOW, objetivo=hora.paciente.usuario,
            detalle=_detalle_hora(hora))  # DEF-07 (RN-11)
