"""
B-14 · Pantallas de la lista de espera (RF-06, RN-17).

Paciente/tutor: inscribirse, ver su lugar, aceptar o rechazar un cupo ofrecido.
SOME: ver la fila, inscribir en ventanilla, aceptar por teléfono y ver los cupos
liberados de ventanilla. Administrador: indicadores para calibrar los tramos.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from agendaApp.models import BloqueHorario, Especialidad
from agendaApp.servicios import ReglaNegocioError
from agendaApp.views import requiere_vigente
from autenticacionApp.forms import IngresoRutForm
from autenticacionApp.models import Paciente, Usuario
from autenticacionApp.sesion import requiere_administrador, requiere_paciente, requiere_some
from proyectoHoraSalud.configuracion_sistema import ConfiguracionSistema

from . import servicios
from .models import EsperaPaciente, OfertaCupo


def _quien(request):
    return 'Tutor' if request.user.tipo_usuario == Usuario.Tipo.TUTOR else 'Paciente'


def _reglas():
    config = ConfiguracionSistema()
    return {
        'plazo_largo': servicios.texto_plazo(config.plazo_tramo_largo_min),
        'plazo_corto': servicios.texto_plazo(config.plazo_confirmacion_reasignacion_min),
        'horas_largo': config.lista_tramo_largo_horas, 'horas_corto': config.lista_tramo_corto_horas,
        'desde': config.avisos_desde_hora, 'hasta': config.avisos_hasta_hora,
        'alerta': config.ofertas_sin_respuesta_alerta,
    }


# ---------- Paciente / tutor ----------

@requiere_paciente
def mi_lista(request):
    esperas = EsperaPaciente.objects.filter(paciente=request.paciente).select_related('especialidad')
    filas = [{'espera': e, 'lugar': servicios.posicion(e), 'total': servicios.fila(e.especialidad).count()}
             for e in esperas]
    return render(request, 'listaEsperaApp/mi_lista.html', {
        'filas': filas, 'ofertas': servicios.ofertas_pendientes(request.paciente), 'reglas': _reglas()})


@require_POST
@requiere_paciente
@requiere_vigente
def inscribirme(request, especialidad_id):
    especialidad = get_object_or_404(Especialidad, pk=especialidad_id)
    try:
        espera = servicios.inscribir(request.paciente, especialidad, EsperaPaciente.Origen.APP, request=request)
    except ReglaNegocioError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f'Quedaste en la lista de espera de {especialidad}, en el lugar '
                                  f'{servicios.posicion(espera)}. Te avisaremos si se libera una hora.')
    return redirect('mi_lista_espera')


@require_POST
@requiere_paciente
def salir_de_lista(request, espera_id):
    espera = get_object_or_404(EsperaPaciente, pk=espera_id, paciente=request.paciente)  # RN-07
    nombre = str(espera.especialidad)
    servicios.salir(espera, quien=_quien(request), request=request)
    messages.info(request, f'Saliste de la lista de espera de {nombre}.')
    return redirect('mi_lista_espera')


@requiere_paciente
def oferta(request, oferta_id):
    oferta = get_object_or_404(OfertaCupo.objects.select_related(
        'cupo__bloque__agenda__especialidad', 'cupo__bloque__agenda__profesional__usuario'),
        pk=oferta_id, paciente=request.paciente)  # RN-07: solo la propia (o de quien se tiene a cargo)
    if request.method == 'POST':
        try:
            if request.POST.get('accion') == 'aceptar':
                hora = servicios.aceptar(oferta.pk, quien=_quien(request), request=request)
                messages.success(request, '¡Listo! La hora quedó a tu nombre.')
                return redirect('hora_lista', hora_id=hora.pk)
            servicios.rechazar(oferta.pk, quien=_quien(request))
            messages.info(request, 'Entendido. No pierdes tu lugar en la lista de espera: '
                                   'te avisaremos cuando se libere otra hora.')
        except ReglaNegocioError as error:
            messages.error(request, str(error))
        return redirect('mi_lista_espera')
    ahora = timezone.now()
    vigente = oferta.estado == OfertaCupo.Estado.PENDIENTE and oferta.vence_en > ahora
    return render(request, 'listaEsperaApp/oferta.html', {
        'oferta': oferta, 'bloque': oferta.cupo.bloque, 'vigente': vigente,
        'segundos': max(0, int((oferta.vence_en - ahora).total_seconds())) if vigente else 0})


# ---------- SOME ----------

def _url_some(especialidad_id):
    return f"{reverse('some_lista_espera')}?especialidad={especialidad_id}"


@requiere_some
def some_lista(request):
    especialidades = list(Especialidad.objects.order_by('tipo', 'nombre'))
    especialidad = next((e for e in especialidades if str(e.pk) == request.GET.get('especialidad')),
                        especialidades[0] if especialidades else None)
    rut_form = IngresoRutForm(request.POST or None)
    if request.method == 'POST' and especialidad:
        if rut_form.is_valid():
            paciente = Paciente.objects.filter(usuario__rut=rut_form.cleaned_data['rut']).first()
            if paciente is None:
                messages.error(request, 'Ese RUT no está inscrito en HoraSalud. Primero entrégale su código '
                                        '(Activar huella).')
            else:
                try:
                    espera = servicios.inscribir(paciente, especialidad, EsperaPaciente.Origen.SOME, request=request)
                    messages.success(request, f'{paciente.usuario.get_full_name()} quedó en el lugar '
                                              f'{servicios.posicion(espera)} de {especialidad}.')
                except ReglaNegocioError as error:
                    messages.error(request, str(error))
        else:
            messages.error(request, 'Revisa el RUT.')
        return redirect(_url_some(especialidad.pk))
    filas, ofertas = [], {}
    if especialidad:
        ofertas = {o.paciente_id: o for o in OfertaCupo.objects.filter(
            estado=OfertaCupo.Estado.PENDIENTE, cupo__especialidad=especialidad).select_related('cupo__bloque__agenda')}
        alerta = ConfiguracionSistema().ofertas_sin_respuesta_alerta
        filas = [{'lugar': i, 'espera': e, 'oferta': ofertas.get(e.paciente_id),
                  'alerta': e.ofertas_sin_respuesta >= alerta}
                 for i, e in enumerate(servicios.fila(especialidad), start=1)]
    liberados = (BloqueHorario.objects.filter(tipo_cupo=BloqueHorario.TipoCupo.LIBERADO,
                                              estado=BloqueHorario.Estado.DISPONIBLE,
                                              agenda__fecha__gte=timezone.localdate())
                 .select_related('agenda__especialidad', 'agenda__profesional__usuario')
                 .order_by('agenda__fecha', 'hora_inicio'))
    ahora = timezone.localtime()
    liberados = [b for b in liberados if servicios.inicio_bloque(b) > ahora]
    return render(request, 'listaEsperaApp/some_lista.html', {
        'especialidades': especialidades, 'especialidad': especialidad, 'filas': filas,
        'rut_form': rut_form, 'liberados': liberados, 'reglas': _reglas()})


@require_POST
@requiere_some
def some_quitar(request, espera_id):
    espera = get_object_or_404(EsperaPaciente.objects.select_related('paciente__usuario'), pk=espera_id)
    nombre, especialidad_id = espera.paciente.usuario.get_full_name(), espera.especialidad_id
    servicios.salir(espera, quien='SOME', request=request)
    messages.info(request, f'{nombre} salió de la lista de espera.')
    return redirect(_url_some(especialidad_id))


@require_POST
@requiere_some
def some_oferta(request, oferta_id, accion):
    """El SOME llama por teléfono al paciente y registra su respuesta."""
    oferta = get_object_or_404(OfertaCupo.objects.select_related('paciente__usuario', 'cupo'), pk=oferta_id)
    nombre = oferta.paciente.usuario.get_full_name()
    try:
        if accion == 'aceptar':
            hora = servicios.aceptar(oferta.pk, quien='SOME (por teléfono)', request=request)
            messages.success(request, f'Hora asignada a {nombre}: {hora.bloque.agenda.fecha:%d-%m} a las '
                                      f'{hora.bloque.hora_inicio:%H:%M}.')
        elif accion == 'rechazar':
            servicios.rechazar(oferta.pk, quien='SOME (por teléfono)')
            messages.info(request, f'{nombre} no puede: conserva su lugar y el cupo pasó al siguiente.')
    except ReglaNegocioError as error:
        messages.error(request, str(error))
    return redirect(_url_some(oferta.cupo.especialidad_id))


# ---------- Administrador ----------

@requiere_administrador
def indicadores(request):
    return render(request, 'listaEsperaApp/indicadores.html', {**servicios.indicadores(), 'reglas': _reglas()})
