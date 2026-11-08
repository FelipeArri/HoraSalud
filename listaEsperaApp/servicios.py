"""
B-14 · Reglas de la lista de espera (RF-06, RN-17).

Cuando un paciente cancela, el cupo se trata según cuánto falta para la hora:

  Más de 48 h   -> se ofrece EN ORDEN a la fila de la app; 1 hora para responder.
  24 a 48 h     -> se ofrece EN ORDEN, más rápido; 10 minutos para responder.
  Menos de 24 h -> "cupo liberado de ventanilla": lo entrega el SOME. (El No-Show
                   no entra aquí: su hora ya pasó y el tiempo lo usa la ventanilla.)

Reglas de equidad: el orden de la fila se respeta siempre. Si alguien no puede o
no responde, conserva su lugar; ese cupo pasa al siguiente. Tras 3 ofertas
seguidas sin respuesta, el SOME ve una marca para llamarlo (no se le castiga).
Si nadie de la fila lo toma, el cupo queda libre en la app para cualquiera.
Los avisos solo se envían de 08:00 a 20:00. Todos los valores están en
ConfiguracionSistema (Singleton) y son parámetros a calibrar con las estadísticas.

Concurrencia (RN-02): aceptar bloquea el bloque (select_for_update) y la base de
datos impide dos horas vigentes en el mismo bloque. El segundo recibe un mensaje claro.
"""
import logging
from dataclasses import dataclass, field
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, F, Max, Q
from django.utils import timezone

from agendaApp import prevision
from agendaApp.models import BloqueHorario, Especialidad, Hora
from agendaApp.servicios import ReglaNegocioError, _detalle_hora, horas_vigentes, inicio_bloque
from autenticacionApp.models import Paciente, RegistroAuditoria
from autenticacionApp.personal import auditar
from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema

from .models import CupoLiberado, EsperaPaciente, OfertaCupo

logger = logging.getLogger(__name__)
Accion = RegistroAuditoria.Accion
Tramo = OfertaCupo.Tramo
Resultado = CupoLiberado.Resultado
VENTANILLA = 'ventanilla'


# ---------- Tramos y horario de avisos ----------

def horas_de_anticipacion(bloque, ahora=None):
    return (inicio_bloque(bloque) - (ahora or timezone.now())).total_seconds() / 3600


def tramo_de(bloque, ahora=None):
    config, horas = ConfiguracionSistema(), horas_de_anticipacion(bloque, ahora)
    if horas >= config.lista_tramo_largo_horas:
        return Tramo.LARGO
    if horas >= config.lista_tramo_corto_horas:
        return Tramo.CORTO
    return VENTANILLA


def plazo_minutos(tramo):
    config = ConfiguracionSistema()
    return config.plazo_tramo_largo_min if tramo == Tramo.LARGO else config.plazo_confirmacion_reasignacion_min


def texto_plazo(minutos):
    if minutos % 60 == 0:
        horas = minutos // 60
        return f'{horas} hora' + ('s' if horas > 1 else '')
    return f'{minutos} minutos'


def en_horario_de_avisos(ahora, plazo_min):
    """De 08:00 a 20:00, y con tiempo para responder antes de las 20:00 (no se despierta a nadie)."""
    config, local = ConfiguracionSistema(), timezone.localtime(ahora)
    desde = local.replace(hour=config.avisos_desde_hora, minute=0, second=0, microsecond=0)
    hasta = local.replace(hour=config.avisos_hasta_hora, minute=0, second=0, microsecond=0)
    return desde <= local and local + timedelta(minutes=plazo_min) <= hasta


# ---------- La fila ----------

def fila(especialidad):
    return (EsperaPaciente.objects.filter(especialidad=especialidad)
            .select_related('paciente__usuario', 'paciente__tutor', 'paciente__sector', 'especialidad')
            .order_by('orden', 'creado_en', 'pk'))


def posicion(espera):
    ids = list(fila(espera.especialidad).values_list('pk', flat=True))
    return ids.index(espera.pk) + 1 if espera.pk in ids else None


def inscribir(paciente, especialidad, origen=EsperaPaciente.Origen.APP, request=None):
    """El paciente queda último en la fila de esa especialidad."""
    if paciente.estado_inscripcion != Paciente.Estado.VIGENTE:
        raise ReglaNegocioError(prevision.mensaje_no_vigente(paciente))  # RN-16
    if horas_vigentes(paciente).filter(bloque__agenda__especialidad=especialidad).exists():
        raise ReglaNegocioError(f'Ya tiene una hora vigente en {especialidad}: no necesita la lista de espera.')
    try:
        with transaction.atomic():
            ultimo = EsperaPaciente.objects.filter(especialidad=especialidad).aggregate(m=Max('orden'))['m'] or 0
            espera = EsperaPaciente.objects.create(especialidad=especialidad, paciente=paciente,
                                                   orden=ultimo + 1, inscrito_por=origen)
    except IntegrityError:
        raise ReglaNegocioError(f'Ya está en la lista de espera de {especialidad}.')
    auditar(request, Accion.ESPERA_ALTA, objetivo=paciente.usuario,
            detalle=f'{especialidad} · lugar {posicion(espera)} · {espera.get_inscrito_por_display()}')
    return espera


def salir(espera, quien='Paciente', request=None):
    """Sale de la fila. Si tenía un cupo ofrecido, ese cupo pasa al siguiente."""
    pendientes = list(OfertaCupo.objects.filter(paciente=espera.paciente, estado=OfertaCupo.Estado.PENDIENTE,
                                                cupo__especialidad=espera.especialidad).select_related('cupo'))
    OfertaCupo.objects.filter(pk__in=[o.pk for o in pendientes]).update(
        estado=OfertaCupo.Estado.ANULADA, respondida_en=timezone.now(), respondida_por=quien)
    auditar(request, Accion.ESPERA_BAJA, objetivo=espera.paciente.usuario,
            detalle=f'{quien} · {espera.especialidad}')
    espera.delete()
    for oferta in pendientes:
        ofrecer_siguiente(oferta.cupo)


def quitar_al_tener_hora(hora):
    """Si el paciente consigue hora en la especialidad (por cualquier vía), sale de esa fila."""
    especialidad_id = hora.bloque.agenda.especialidad_id
    EsperaPaciente.objects.filter(paciente_id=hora.paciente_id, especialidad_id=especialidad_id).delete()
    (OfertaCupo.objects.filter(paciente_id=hora.paciente_id, estado=OfertaCupo.Estado.PENDIENTE,
                               cupo__especialidad_id=especialidad_id)
     .exclude(cupo__bloque_id=hora.bloque_id)
     .update(estado=OfertaCupo.Estado.ANULADA, respondida_en=timezone.now()))  # el cupo sigue con procesar()


# ---------- Un cupo se libera (Observer) ----------

def registrar_cupo_liberado(bloque, ahora=None):
    """Receptor de agendaApp.eventos.cupo_liberado. Devuelve el CupoLiberado o None."""
    ahora = ahora or timezone.now()
    bloque = BloqueHorario.objects.select_related('agenda__especialidad').get(pk=bloque.pk)
    if bloque.tipo_cupo != BloqueHorario.TipoCupo.PROGRAMADO or bloque.estado != BloqueHorario.Estado.DISPONIBLE:
        return None
    especialidad = bloque.agenda.especialidad
    if not EsperaPaciente.objects.filter(especialidad=especialidad).exists():
        return None  # nadie espera: el cupo sigue libre en la app, como siempre
    horas = horas_de_anticipacion(bloque, ahora)
    if horas <= 0:
        return None
    cupo = CupoLiberado.objects.create(bloque=bloque, especialidad=especialidad, anticipacion_horas=round(horas, 1))
    if tramo_de(bloque, ahora) == VENTANILLA:
        _cerrar(cupo, Resultado.VENTANILLA, ahora)
    else:
        BloqueHorario.objects.filter(pk=bloque.pk).update(estado=BloqueHorario.Estado.EN_OFERTA)
        ofrecer_siguiente(cupo, ahora)
    return cupo


def _cerrar(cupo, resultado, ahora):
    """Termina el proceso del cupo: a ventanilla o libre en la app."""
    cambios = {'estado': BloqueHorario.Estado.DISPONIBLE}
    if resultado == Resultado.VENTANILLA:
        cambios['tipo_cupo'] = BloqueHorario.TipoCupo.LIBERADO  # deja de verse en la app
    (BloqueHorario.objects.filter(pk=cupo.bloque_id)
     .filter(Q(estado=BloqueHorario.Estado.EN_OFERTA) | Q(estado=BloqueHorario.Estado.DISPONIBLE))
     .update(**cambios))
    CupoLiberado.objects.filter(pk=cupo.pk).update(resultado=resultado, resuelto_en=ahora)
    cupo.resultado = resultado


def _siguiente_en_fila(cupo, bloque):
    """Primera persona de la fila que puede tomar el cupo y aún no lo ha recibido."""
    ya_ofrecido = set(cupo.ofertas.values_list('paciente_id', flat=True))
    sector_del_profesional = bloque.agenda.profesional.sector_id
    especialidad = bloque.agenda.especialidad
    for lugar, espera in enumerate(fila(especialidad), start=1):
        paciente = espera.paciente
        if paciente.pk in ya_ofrecido or paciente.estado_inscripcion != Paciente.Estado.VIGENTE:
            continue
        if sector_del_profesional and paciente.sector_id != sector_del_profesional:
            continue  # DEF-06: solo agendas de su sector o de profesionales sin sector
        if horas_vigentes(paciente).filter(bloque__agenda__especialidad=especialidad).exists():
            continue  # RN-01
        return espera, lugar
    return None, None


def _crear_oferta(cupo, ahora):
    with transaction.atomic():
        bloque = (BloqueHorario.objects.select_for_update()
                  .select_related('agenda__especialidad', 'agenda__profesional').get(pk=cupo.bloque_id))
        cupo.refresh_from_db()
        if cupo.resultado != Resultado.EN_CURSO or cupo.ofertas.filter(estado=OfertaCupo.Estado.PENDIENTE).exists():
            return None
        if bloque.estado != BloqueHorario.Estado.EN_OFERTA:
            _cerrar(cupo, Resultado.LIBRE_APP, ahora)  # alguien lo cambió a mano (por ejemplo, desde /admin/)
            return None
        tramo = tramo_de(bloque, ahora)
        if tramo == VENTANILLA:
            _cerrar(cupo, Resultado.VENTANILLA, ahora)
            return None
        plazo = plazo_minutos(tramo)
        if not en_horario_de_avisos(ahora, plazo):
            return None  # se retoma a las 08:00 (procesar)
        espera, lugar = _siguiente_en_fila(cupo, bloque)
        if espera is None:
            _cerrar(cupo, Resultado.LIBRE_APP, ahora)
            return None
        return OfertaCupo.objects.create(cupo=cupo, paciente=espera.paciente, posicion=lugar, tramo=tramo,
                                         enviada_en=ahora, vence_en=ahora + timedelta(minutes=plazo))


def ofrecer_siguiente(cupo, ahora=None):
    """Ofrece el cupo a la siguiente persona de la fila y le envía el aviso (fuera de la transacción)."""
    ahora = ahora or timezone.now()
    oferta = _crear_oferta(cupo, ahora)
    if oferta:
        from notificacionesApp.envio import avisar
        minutos = plazo_minutos(oferta.tramo)
        avisar(oferta.paciente,
               f'Se liberó una hora para ti en el CESFAM. Tienes {texto_plazo(minutos)} para aceptarla. '
               'Entra a HoraSalud.', url=f'/lista-espera/oferta/{oferta.pk}/', ttl=minutos * 60)
    return oferta


# ---------- Respuestas ----------

def _vencer(oferta):
    oferta.estado = OfertaCupo.Estado.VENCIDA
    oferta.save(update_fields=['estado'])
    EsperaPaciente.objects.filter(paciente_id=oferta.paciente_id, especialidad_id=oferta.cupo.especialidad_id
                                  ).update(ofertas_sin_respuesta=F('ofertas_sin_respuesta') + 1)


def aceptar(oferta_id, quien='Paciente', request=None, ahora=None):
    """El paciente (o su tutor, o el SOME por teléfono) acepta. Devuelve la Hora creada."""
    ahora = ahora or timezone.now()
    error, hora, oferta = None, None, None
    with transaction.atomic():
        cupo_id = OfertaCupo.objects.values_list('cupo__bloque_id', flat=True).get(pk=oferta_id)
        bloque = BloqueHorario.objects.select_for_update().select_related('agenda__especialidad').get(pk=cupo_id)
        oferta = OfertaCupo.objects.select_related('cupo', 'paciente__usuario').get(pk=oferta_id)  # se relee con el bloqueo
        paciente = oferta.paciente
        if oferta.estado == OfertaCupo.Estado.ACEPTADA:
            error = 'Esta hora ya estaba aceptada.'
        elif oferta.estado != OfertaCupo.Estado.PENDIENTE:
            error = 'Este cupo ya no está disponible. Sigue en su lugar de la lista de espera.'
        elif ahora >= oferta.vence_en:
            _vencer(oferta)
            error = 'Se acabó el plazo para aceptar este cupo. Sigue en su lugar de la lista de espera.'
        elif bloque.estado != BloqueHorario.Estado.EN_OFERTA:
            error = 'Ese cupo ya fue tomado. Sigue en su lugar de la lista de espera.'
        elif paciente.estado_inscripcion != Paciente.Estado.VIGENTE:
            error = prevision.mensaje_no_vigente(paciente)
        elif horas_vigentes(paciente).filter(bloque__agenda__especialidad=bloque.agenda.especialidad).exists():
            error = f'Ya tiene una hora vigente en {bloque.agenda.especialidad}.'  # RN-01
        else:
            try:
                with transaction.atomic():
                    hora = Hora.objects.create(bloque=bloque, paciente=paciente)
            except IntegrityError:  # RN-02: la base de datos impide la doble reserva
                error = 'Ese cupo ya fue tomado por otra persona. Sigue en su lugar de la lista de espera.'
            else:
                oferta.estado, oferta.respondida_en, oferta.respondida_por = OfertaCupo.Estado.ACEPTADA, ahora, quien
                oferta.save(update_fields=['estado', 'respondida_en', 'respondida_por'])
                CupoLiberado.objects.filter(pk=oferta.cupo_id).update(resultado=Resultado.REASIGNADO,
                                                                      resuelto_en=ahora)
    if error:
        if oferta and oferta.estado == OfertaCupo.Estado.VENCIDA:
            ofrecer_siguiente(oferta.cupo, ahora)
        raise ReglaNegocioError(error)
    from agendaApp.gestion_agendas import resolver_indicacion_al_reservar
    resolver_indicacion_al_reservar(hora)  # P-10
    auditar(request, Accion.CUPO_ACEPTADO, objetivo=paciente.usuario,
            detalle=f'{quien} · {_detalle_hora(hora)} · lugar {oferta.posicion} de la fila')
    return hora


def rechazar(oferta_id, quien='Paciente', ahora=None):
    """'No puedo': conserva su lugar en la fila y el cupo pasa al siguiente."""
    ahora = ahora or timezone.now()
    with transaction.atomic():
        oferta = OfertaCupo.objects.select_for_update().select_related('cupo').get(pk=oferta_id)
        if oferta.estado != OfertaCupo.Estado.PENDIENTE:
            return oferta
        oferta.estado, oferta.respondida_en, oferta.respondida_por = OfertaCupo.Estado.RECHAZADA, ahora, quien
        oferta.save(update_fields=['estado', 'respondida_en', 'respondida_por'])
        EsperaPaciente.objects.filter(paciente_id=oferta.paciente_id, especialidad_id=oferta.cupo.especialidad_id
                                      ).update(ofertas_sin_respuesta=0)  # respondió: se borra la marca
    ofrecer_siguiente(oferta.cupo, ahora)
    return oferta


def procesar(ahora=None):
    """Vence ofertas sin respuesta y sigue con la fila. Lo llama el middleware y el comando."""
    ahora = ahora or timezone.now()
    vencidas = 0
    for oferta in OfertaCupo.objects.filter(estado=OfertaCupo.Estado.PENDIENTE, vence_en__lte=ahora
                                            ).select_related('cupo'):
        _vencer(oferta)
        vencidas += 1
    nuevas = sum(1 for cupo in CupoLiberado.objects.filter(resultado=Resultado.EN_CURSO)
                 if ofrecer_siguiente(cupo, ahora))
    return {'vencidas': vencidas, 'ofertas_nuevas': nuevas}


def ofertas_pendientes(paciente, ahora=None):
    ahora = ahora or timezone.now()
    return (OfertaCupo.objects.filter(paciente=paciente, estado=OfertaCupo.Estado.PENDIENTE, vence_en__gt=ahora)
            .select_related('cupo__bloque__agenda__especialidad', 'cupo__bloque__agenda__profesional__usuario'))


# ---------- Estadísticas (para calibrar los tramos) ----------

RANGOS = [(0, 24, 'Menos de 24 h'), (24, 48, '24 a 48 h'), (48, 72, '48 a 72 h'),
          (72, 168, '3 a 7 días'), (168, 10 ** 6, 'Más de 7 días')]


@dataclass
class FilaIndicador:
    nombre: str
    datos: dict = field(default_factory=dict)


def _pct(parte, total):
    return round(100 * parte / total) if total else None


def indicadores():
    """Cantidades sin datos personales (Ley 19.628): sirven para calibrar los tramos (RN-17)."""
    por_tramo = []
    for tramo in Tramo:
        ofertas = OfertaCupo.objects.filter(tramo=tramo)
        cuenta = {e.value: ofertas.filter(estado=e).count() for e in OfertaCupo.Estado}
        respondidas = cuenta['aceptada'] + cuenta['rechazada'] + cuenta['vencida']
        tiempos = [(r - e).total_seconds() for e, r in ofertas.filter(estado__in=['aceptada', 'rechazada'])
                   .values_list('enviada_en', 'respondida_en') if r]
        demora = sum(tiempos) / len(tiempos) if tiempos else None  # se calcula aquí: igual en MySQL y SQLite
        por_tramo.append(FilaIndicador(tramo.label, {
            'total': ofertas.count(), **cuenta,
            'pct_aceptadas': _pct(cuenta['aceptada'], respondidas),
            'pct_vencidas': _pct(cuenta['vencida'], respondidas),
            'demora_min': round(demora / 60, 1) if demora is not None else None,
        }))
    por_rango = []
    for desde, hasta, nombre in RANGOS:
        cupos = CupoLiberado.objects.filter(anticipacion_horas__gte=desde, anticipacion_horas__lt=hasta)
        cuenta = {r.value: cupos.filter(resultado=r).count() for r in Resultado}
        por_rango.append(FilaIndicador(nombre, {'total': cupos.count(), **cuenta,
                                                'pct_reasignados': _pct(cuenta['reasignado'], cupos.count())}))
    total_cupos = CupoLiberado.objects.count()
    reasignados = CupoLiberado.objects.filter(resultado=Resultado.REASIGNADO).count()
    filas = (Especialidad.objects.annotate(
        en_espera=Count('esperapaciente', distinct=True),
        sin_responder=Count('esperapaciente', filter=Q(
            esperapaciente__ofertas_sin_respuesta__gte=ConfiguracionSistema().ofertas_sin_respuesta_alerta),
            distinct=True))
        .filter(en_espera__gt=0).order_by('nombre'))
    return {'por_tramo': por_tramo, 'por_rango': por_rango, 'filas': filas, 'total_cupos': total_cupos,
            'reasignados': reasignados, 'pct_reasignados': _pct(reasignados, total_cupos)}
