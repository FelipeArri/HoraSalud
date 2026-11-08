"""
B-21 · Gestión de agendas (RN-02, RN-05, RN-13, RF-04, RF-05).

- La Dirección (Administrador CESFAM) carga la plantilla semanal de cada profesional,
  genera las agendas de las próximas semanas, duplica la semana anterior y registra ausencias.
- Ausencia: los bloques quedan Bloqueados y las horas vigentes pasan a "Suspendida por el
  CESFAM", con motivo, aviso al paciente y prioridad en la lista de espera.
- El SOME da horas en ventanilla (morbilidad del día) y sobrecupos. Nunca aparecen en la app.
- El profesional agenda el próximo control o lo indica para que el paciente lo pida (P-10).
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

from autenticacionApp.models import Paciente, RegistroAuditoria
from autenticacionApp.personal import auditar

from .models import (Agenda, AusenciaProfesional, BloqueHorario, Hora, IndicacionControl,
                     PlantillaAgenda)
from .servicios import ESTADOS_VIGENTES, ReglaNegocioError, horas_vigentes

Accion = RegistroAuditoria.Accion


def lunes_de(dia):
    return dia - timedelta(days=dia.weekday())


def esta_ausente(profesional, dia):
    return AusenciaProfesional.objects.filter(profesional=profesional, desde__lte=dia, hasta__gte=dia).exists()


def _crear_bloques(agenda, inicio, fin, duracion, tipo_cupo):
    creados = 0
    actual = datetime.combine(agenda.fecha, inicio)
    limite = datetime.combine(agenda.fecha, fin)
    while actual + timedelta(minutes=duracion) <= limite:
        siguiente = actual + timedelta(minutes=duracion)
        _, nuevo = BloqueHorario.objects.get_or_create(
            agenda=agenda, hora_inicio=actual.time(),
            defaults={'hora_fin': siguiente.time(), 'tipo_cupo': tipo_cupo})
        creados += nuevo
        actual = siguiente
    return creados


# ---------- Plantilla y generación ----------

def validar_plantilla(plantilla):
    if plantilla.hora_fin <= plantilla.hora_inicio:
        raise ReglaNegocioError('La hora de término debe ser posterior a la de inicio.')
    if not 5 <= plantilla.duracion_min <= 120:
        raise ReglaNegocioError('Cada bloque debe durar entre 5 y 120 minutos.')
    choque = (PlantillaAgenda.objects.filter(profesional=plantilla.profesional, dia_semana=plantilla.dia_semana,
                                             activa=True, hora_inicio__lt=plantilla.hora_fin,
                                             hora_fin__gt=plantilla.hora_inicio)
              .exclude(pk=plantilla.pk))
    if choque.exists():
        raise ReglaNegocioError(f'Se cruza con otro horario del mismo día: {choque.first()}.')


@transaction.atomic
def generar_agendas(desde=None, semanas=4, profesional=None, request=None):
    """Crea agendas y bloques desde las plantillas activas. No duplica lo que ya existe."""
    desde = desde or timezone.localdate()
    plantillas = PlantillaAgenda.objects.filter(activa=True).select_related('profesional', 'especialidad')
    if profesional:
        plantillas = plantillas.filter(profesional=profesional)
    creados = 0
    for i in range(semanas * 7):
        dia = desde + timedelta(days=i)
        for plantilla in plantillas:
            if plantilla.dia_semana != dia.weekday() or esta_ausente(plantilla.profesional, dia):
                continue
            agenda, _ = Agenda.objects.get_or_create(profesional=plantilla.profesional,
                                                     especialidad=plantilla.especialidad, fecha=dia)
            creados += _crear_bloques(agenda, plantilla.hora_inicio, plantilla.hora_fin,
                                      plantilla.duracion_min, plantilla.tipo_cupo)
    if request:
        auditar(request, Accion.AGENDA, detalle=f'Generó {creados} bloques ({semanas} semana(s) desde {desde:%d-%m-%Y})')
    return creados


@transaction.atomic
def duplicar_semana_anterior(profesional, lunes_destino, request=None):
    """Copia los bloques (sin pacientes ni sobrecupos) de la semana anterior a la semana destino."""
    lunes_destino = lunes_de(lunes_destino)
    origen = lunes_destino - timedelta(days=7)
    creados = 0
    agendas = Agenda.objects.filter(profesional=profesional, fecha__range=(origen, origen + timedelta(days=6)))
    for agenda in agendas:
        dia = agenda.fecha + timedelta(days=7)
        if esta_ausente(profesional, dia):
            continue
        nueva, _ = Agenda.objects.get_or_create(profesional=profesional, especialidad=agenda.especialidad, fecha=dia)
        for bloque in agenda.bloques.exclude(tipo_cupo=BloqueHorario.TipoCupo.SOBRECUPO):
            _, nuevo = BloqueHorario.objects.get_or_create(
                agenda=nueva, hora_inicio=bloque.hora_inicio,
                defaults={'hora_fin': bloque.hora_fin, 'tipo_cupo': bloque.tipo_cupo})
            creados += nuevo
    if request:
        auditar(request, Accion.AGENDA, objetivo=profesional.usuario,
                detalle=f'Duplicó la semana del {origen:%d-%m-%Y} ({creados} bloques)')
    return creados


# ---------- Ausencias ----------

@dataclass
class ResultadoAusencia:
    ausencia: AusenciaProfesional
    bloques_bloqueados: int
    horas_suspendidas: int


@transaction.atomic
def registrar_ausencia(profesional, desde, hasta, motivo, detalle='', request=None):
    from listaEsperaApp.models import EsperaPaciente
    from notificacionesApp.models import RegistroNotificacion

    if hasta < desde:
        raise ReglaNegocioError('La fecha "hasta" no puede ser anterior a "desde".')
    ausencia = AusenciaProfesional.objects.create(
        profesional=profesional, desde=desde, hasta=hasta, motivo=motivo, detalle=detalle,
        registrada_por=request.user if request else None)
    bloques = BloqueHorario.objects.filter(agenda__profesional=profesional, agenda__fecha__range=(desde, hasta))
    bloqueados = bloques.exclude(estado=BloqueHorario.Estado.BLOQUEADO).update(estado=BloqueHorario.Estado.BLOQUEADO)
    texto = f'CESFAM: profesional ausente ({ausencia.get_motivo_display().lower()})'
    suspendidas = 0
    for hora in Hora.objects.filter(bloque__in=bloques, estado__in=ESTADOS_VIGENTES).select_related(
            'bloque__agenda', 'paciente'):
        hora.estado = Hora.Estado.SUSPENDIDA
        hora.motivo_cancelacion = texto[:200]  # RN-05
        hora.save()
        RegistroNotificacion.objects.create(hora=hora, canal=RegistroNotificacion.Canal.APP)  # RN-13
        # Prioridad para reagendar: primero en la lista de espera de su especialidad
        especialidad = hora.bloque.agenda.especialidad
        EsperaPaciente.objects.filter(especialidad=especialidad).update(orden=F('orden') + 1)
        EsperaPaciente.objects.update_or_create(especialidad=especialidad, paciente=hora.paciente,
                                                defaults={'orden': 1,
                                                          'inscrito_por': EsperaPaciente.Origen.CESFAM})
        suspendidas += 1
    if request:
        auditar(request, Accion.AUSENCIA, objetivo=profesional.usuario,
                detalle=f'{ausencia.get_motivo_display()} {desde:%d-%m} a {hasta:%d-%m}: '
                        f'{bloqueados} bloques, {suspendidas} horas suspendidas')
    return ResultadoAusencia(ausencia, bloqueados, suspendidas)


def horas_suspendidas_sin_reagendar(paciente):
    """Avisos para el paciente (RN-13): horas suspendidas por el CESFAM aún sin nueva hora."""
    hoy = timezone.localdate()
    suspendidas = (Hora.objects.filter(paciente=paciente, estado=Hora.Estado.SUSPENDIDA,
                                       bloque__agenda__fecha__gte=hoy - timedelta(days=7))
                   .select_related('bloque__agenda__especialidad', 'bloque__agenda__profesional__usuario'))
    con_hora = set(horas_vigentes(paciente).values_list('bloque__agenda__especialidad', flat=True))
    return [h for h in suspendidas if h.bloque.agenda.especialidad_id not in con_hora]


# ---------- Ventanilla SOME (morbilidad y sobrecupo) ----------

def _paciente_vigente(paciente):
    from . import prevision
    prevision.revalidar(paciente)
    if paciente.estado_inscripcion != Paciente.Estado.VIGENTE:
        raise ReglaNegocioError(prevision.mensaje_no_vigente(paciente))  # RN-16


def _sin_hora_ese_dia(paciente, agenda):
    if Hora.objects.filter(paciente=paciente, estado__in=ESTADOS_VIGENTES,
                           bloque__agenda__fecha=agenda.fecha,
                           bloque__agenda__especialidad=agenda.especialidad).exists():
        raise ReglaNegocioError(f'El paciente ya tiene hora ese día en {agenda.especialidad}.')


@transaction.atomic
def dar_hora_ventanilla(paciente, bloque_id, request=None):
    """SOME entrega un bloque libre (morbilidad del día u otro) a un paciente presente en ventanilla."""
    _paciente_vigente(paciente)
    bloque = BloqueHorario.objects.select_for_update().select_related('agenda__especialidad').get(pk=bloque_id)
    if bloque.estado != BloqueHorario.Estado.DISPONIBLE:
        raise ReglaNegocioError('Ese bloque ya no está disponible.')
    _sin_hora_ese_dia(paciente, bloque.agenda)
    hora = Hora.objects.create(bloque=bloque, paciente=paciente, estado=Hora.Estado.CONFIRMADA)
    if request:
        auditar(request, Accion.SOBRECUPO, objetivo=paciente.usuario,
                detalle=f'Ventanilla: {bloque.get_tipo_cupo_display()} {bloque.agenda.fecha:%d-%m} '
                        f'{bloque.hora_inicio:%H:%M} · {bloque.agenda.especialidad}')
    return hora


def hora_sugerida_sobrecupo(agenda):
    ultimo = agenda.bloques.aggregate(fin=Max('hora_fin'))['fin']
    return ultimo or time(8, 0)


@transaction.atomic
def dar_sobrecupo(paciente, agenda, hora_inicio, duracion_min=20, request=None):
    """Bloque extra fuera de la plantilla (solo ventanilla). Queda auditado."""
    _paciente_vigente(paciente)
    if agenda.fecha < timezone.localdate():
        raise ReglaNegocioError('No se pueden dar sobrecupos en días pasados.')
    if esta_ausente(agenda.profesional, agenda.fecha):
        raise ReglaNegocioError('El profesional está ausente ese día.')
    if agenda.bloques.filter(hora_inicio=hora_inicio).exists():
        raise ReglaNegocioError(f'Ya existe un bloque a las {hora_inicio:%H:%M}. Elige otra hora '
                                f'(sugerida: {hora_sugerida_sobrecupo(agenda):%H:%M}).')
    _sin_hora_ese_dia(paciente, agenda)
    fin = (datetime.combine(agenda.fecha, hora_inicio) + timedelta(minutes=duracion_min)).time()
    bloque = BloqueHorario.objects.create(agenda=agenda, hora_inicio=hora_inicio, hora_fin=fin,
                                          tipo_cupo=BloqueHorario.TipoCupo.SOBRECUPO)
    hora = Hora.objects.create(bloque=bloque, paciente=paciente, estado=Hora.Estado.CONFIRMADA)
    if request:
        auditar(request, Accion.SOBRECUPO, objetivo=paciente.usuario,
                detalle=f'Sobrecupo {agenda.fecha:%d-%m} {hora_inicio:%H:%M} · {agenda.especialidad} · '
                        f'{agenda.profesional}')
    return hora


# ---------- Próximo control (P-10) ----------

def bloques_para_control(profesional, desde=None, dias=45):
    desde = desde or timezone.localdate() + timedelta(days=1)
    return (BloqueHorario.objects.filter(agenda__profesional=profesional, estado=BloqueHorario.Estado.DISPONIBLE,
                                         agenda__fecha__range=(desde, desde + timedelta(days=dias)))
            .exclude(tipo_cupo=BloqueHorario.TipoCupo.SOBRECUPO)
            .select_related('agenda__especialidad'))


@transaction.atomic
def agendar_proximo_control(hora_atendida, bloque_id, request=None):
    """El profesional reserva la próxima hora del paciente (puede ser más allá del horizonte de la app)."""
    paciente = hora_atendida.paciente
    _paciente_vigente(paciente)
    profesional = hora_atendida.bloque.agenda.profesional
    bloque = BloqueHorario.objects.select_for_update().select_related('agenda').get(
        pk=bloque_id, agenda__profesional=profesional)
    if bloque.estado != BloqueHorario.Estado.DISPONIBLE or bloque.agenda.fecha <= timezone.localdate():
        raise ReglaNegocioError('Ese bloque ya no está disponible.')
    especialidad = bloque.agenda.especialidad
    if horas_vigentes(paciente).filter(bloque__agenda__especialidad=especialidad).exists():
        raise ReglaNegocioError(f'El paciente ya tiene una hora futura en {especialidad}.')  # RN-01
    hora = Hora.objects.create(bloque=bloque, paciente=paciente)
    IndicacionControl.objects.filter(paciente=paciente, especialidad=especialidad,
                                     resuelta_en__isnull=True).update(resuelta_en=timezone.now())
    if request:
        auditar(request, Accion.PROXIMO_CONTROL, objetivo=paciente.usuario,
                detalle=f'Agendó control {bloque.agenda.fecha:%d-%m-%Y} {bloque.hora_inicio:%H:%M}')
    return hora


def indicar_control(hora_atendida, semanas=4, request=None):
    """El paciente queda con un recordatorio: "pide tu hora de control desde el <fecha>"."""
    agenda = hora_atendida.bloque.agenda
    indicacion = IndicacionControl.objects.create(
        paciente=hora_atendida.paciente, especialidad=agenda.especialidad, indicada_por=agenda.profesional,
        fecha_sugerida=timezone.localdate() + timedelta(weeks=semanas))
    if request:
        auditar(request, Accion.PROXIMO_CONTROL, objetivo=hora_atendida.paciente.usuario,
                detalle=f'Indicó control en {semanas} semana(s) · {agenda.especialidad}')
    return indicacion


def indicaciones_pendientes(paciente):
    return (IndicacionControl.objects.filter(paciente=paciente, resuelta_en__isnull=True)
            .select_related('especialidad'))


def resolver_indicacion_al_reservar(hora):
    IndicacionControl.objects.filter(paciente=hora.paciente, especialidad=hora.bloque.agenda.especialidad,
                                     resuelta_en__isnull=True).update(resuelta_en=timezone.now())


# ---------- Calendario semanal ----------

def semana(profesional, lunes):
    """Días de lunes a sábado con sus bloques y la hora vigente de cada uno (si hay)."""
    lunes = lunes_de(lunes)
    dias = [lunes + timedelta(days=i) for i in range(6)]
    bloques = (BloqueHorario.objects.filter(agenda__profesional=profesional, agenda__fecha__in=dias)
               .select_related('agenda__especialidad', 'hora_vigente__paciente__usuario')
               .order_by('agenda__fecha', 'hora_inicio'))
    por_dia = {d: [] for d in dias}
    for b in bloques:
        por_dia[b.agenda.fecha].append(b)
    ausencias = AusenciaProfesional.objects.filter(profesional=profesional, desde__lte=dias[-1], hasta__gte=dias[0])
    columnas = []
    for d in dias:
        ausencia = next((a for a in ausencias if a.desde <= d <= a.hasta), None)
        if d.weekday() == 5 and not por_dia[d] and not ausencia:
            continue  # sábado solo si tiene algo
        columnas.append({'fecha': d, 'bloques': por_dia[d], 'ausencia': ausencia})
    return columnas


def fecha_o_hoy(texto):
    try:
        return date.fromisoformat(texto) if texto else timezone.localdate()
    except ValueError:
        return timezone.localdate()
