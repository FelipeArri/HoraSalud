"""
Pantallas de agendamiento (D23-C03 wireframes 2, 3 y 4).

Paciente/tutor: inicio, pedir hora (3 pasos), mis horas, cancelar.
SOME: nomina del dia con acciones Atendida / No-Show (RF-05).
"""
from collections import OrderedDict
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from autenticacionApp.models import Paciente
from autenticacionApp.sesion import requiere_paciente, requiere_some

from . import prevision, servicios
from .estados_hora import TransicionInvalida
from .models import Agenda, BloqueHorario, Especialidad, Hora


# ---------- Paciente / tutor ----------

def requiere_vigente(vista):
    """B-19 · RN-16: un paciente No vigente no puede pedir horas por la app."""
    def envoltura(request, *args, **kwargs):
        if request.paciente.estado_inscripcion != Paciente.Estado.VIGENTE:
            messages.error(request, prevision.mensaje_no_vigente(request.paciente))
            return redirect('mi_inicio')
        return vista(request, *args, **kwargs)
    envoltura.__name__ = vista.__name__
    return envoltura


@requiere_paciente
def mi_inicio(request):
    vigentes = servicios.horas_vigentes(request.paciente)
    no_vigente = request.paciente.estado_inscripcion != Paciente.Estado.VIGENTE
    return render(request, 'agendaApp/mi_inicio.html', {
        'aviso_no_vigente': prevision.mensaje_no_vigente(request.paciente) if no_vigente else '',
        'proxima': vigentes.first(),
        'cantidad_vigentes': vigentes.count(),
    })


@requiere_paciente
@requiere_vigente
def pedir_especialidad(request):
    """Paso 1 de 3: elegir especialidad (tabs Medicina general / Programas)."""
    # RN-01: si ya tiene una hora vigente en esa especialidad, se avisa desde el paso 1
    vigentes = {h.bloque.agenda.especialidad_id: h for h in servicios.horas_vigentes(request.paciente)}
    tarjetas = []
    for especialidad in Especialidad.objects.order_by('tipo', 'nombre'):
        libres = servicios.bloques_reservables(especialidad)
        tarjetas.append({'especialidad': especialidad, 'proximo': libres[0] if libres else None,
                         'cantidad': len(libres), 'vigente': vigentes.get(especialidad.pk)})
    return render(request, 'agendaApp/pedir_especialidad.html', {
        'medicina_general': [t for t in tarjetas if t['especialidad'].tipo == Especialidad.Tipo.MEDICINA_GENERAL],
        'programas': [t for t in tarjetas if t['especialidad'].tipo == Especialidad.Tipo.PROGRAMA],
        'paso': 1,
    })


@requiere_paciente
@requiere_vigente
def pedir_bloque(request, especialidad_id):
    """Paso 2 de 3: elegir dia y hora."""
    especialidad = get_object_or_404(Especialidad, pk=especialidad_id)
    libres = servicios.bloques_reservables(especialidad)
    dias = OrderedDict()
    for bloque in libres:
        dias.setdefault(bloque.agenda.fecha, []).append(bloque)
    dia_elegido = request.GET.get('dia')
    try:
        dia_elegido = date.fromisoformat(dia_elegido) if dia_elegido else None
    except ValueError:
        dia_elegido = None
    if dia_elegido not in dias:
        dia_elegido = next(iter(dias), None)
    return render(request, 'agendaApp/pedir_bloque.html', {
        'especialidad': especialidad, 'dias': list(dias), 'dia_elegido': dia_elegido,
        'bloques': dias.get(dia_elegido, []), 'paso': 2,
    })


@requiere_paciente
@requiere_vigente
def pedir_confirmar(request, bloque_id):
    """Paso 3 de 3: resumen y confirmacion."""
    bloque = get_object_or_404(BloqueHorario.objects.select_related(
        'agenda__especialidad', 'agenda__profesional__usuario'), pk=bloque_id)
    if request.method == 'POST':
        try:
            hora = servicios.reservar_hora(request.paciente, bloque.pk)
        except servicios.ReglaNegocioError as error:
            messages.error(request, str(error))
            return redirect('pedir_bloque', especialidad_id=bloque.agenda.especialidad_id)
        return redirect('hora_lista', hora_id=hora.pk)
    return render(request, 'agendaApp/pedir_confirmar.html', {'bloque': bloque, 'paso': 3})


def _hora_del_paciente(request, hora_id):
    # RN-07: solo se puede ver o tocar una hora propia (o de quien se tiene a cargo)
    return get_object_or_404(Hora.objects.select_related(
        'bloque__agenda__especialidad', 'bloque__agenda__profesional__usuario'),
        pk=hora_id, paciente=request.paciente)


@requiere_paciente
def hora_lista(request, hora_id):
    return render(request, 'agendaApp/hora_lista.html', {'hora': _hora_del_paciente(request, hora_id)})


@requiere_paciente
def mis_horas(request):
    hoy = timezone.localdate()
    todas = (Hora.objects.filter(paciente=request.paciente)
             .select_related('bloque__agenda__especialidad', 'bloque__agenda__profesional__usuario'))
    proximas = [h for h in todas if h.estado in servicios.ESTADOS_VIGENTES and h.bloque.agenda.fecha >= hoy]
    historial = [h for h in todas if h not in proximas]
    historial.reverse()
    return render(request, 'agendaApp/mis_horas.html', {'proximas': proximas, 'historial': historial[:10]})


@requiere_paciente
def cancelar(request, hora_id):
    hora = _hora_del_paciente(request, hora_id)
    if request.method == 'POST':
        quien = 'Tutor' if request.user.tipo_usuario == 'tutor' else 'Paciente'
        try:
            servicios.cancelar_hora(hora, request.POST.get('motivo', ''), quien=quien)
        except servicios.ReglaNegocioError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, 'Tu hora fue cancelada. El horario quedó libre para otra persona.')
            return redirect('mis_horas')
    return render(request, 'agendaApp/cancelar.html', {
        'hora': hora, 'motivos': servicios.MOTIVOS_CANCELACION})


@require_POST
@requiere_paciente
def confirmar_asistencia(request, hora_id):
    try:
        servicios.confirmar_asistencia(_hora_del_paciente(request, hora_id))
        messages.success(request, '¡Gracias! Confirmaste que asistirás.')
    except servicios.ReglaNegocioError as error:
        messages.info(request, str(error))
    return redirect('mis_horas')


# ---------- SOME ----------

@requiere_some
def some_nomina(request):
    """Wireframe 4: nomina del dia con RUT y N° de ficha (RF-04, RF-05)."""
    fechas = list(Agenda.objects.filter(fecha__gte=timezone.localdate())
                  .order_by('fecha').values_list('fecha', flat=True).distinct()[:10])
    try:
        dia = date.fromisoformat(request.GET.get('dia', ''))
    except ValueError:
        dia = fechas[0] if fechas else timezone.localdate()
    horas = (Hora.objects.filter(bloque__agenda__fecha=dia)
             .exclude(estado=Hora.Estado.CANCELADA)
             .select_related('paciente__usuario', 'bloque__agenda__especialidad',
                             'bloque__agenda__profesional')
             .order_by('bloque__hora_inicio'))
    filas = [{'hora': h, 'puede_no_show': servicios.puede_marcar_no_show(h)} for h in horas]
    resumen = {
        'total': len(filas),
        'pendientes': sum(1 for f in filas if f['hora'].estado in servicios.ESTADOS_VIGENTES),
        'atendidas': sum(1 for f in filas if f['hora'].estado == Hora.Estado.ATENDIDA),
        'no_show': sum(1 for f in filas if f['hora'].estado == Hora.Estado.NO_SHOW),
    }
    no_vigentes = Paciente.objects.filter(estado_inscripcion=Paciente.Estado.NO_VIGENTE).count()
    return render(request, 'agendaApp/some_nomina.html', {
        'no_vigentes': no_vigentes,
        'dia': dia, 'fechas': fechas, 'filas': filas, 'resumen': resumen, 'hoy': timezone.localdate()})


@require_POST
@requiere_some
def some_accion(request, hora_id, accion):
    hora = get_object_or_404(Hora.objects.select_related('bloque__agenda'), pk=hora_id)
    acciones = {'atendida': servicios.marcar_atendida, 'no-show': servicios.marcar_no_show}
    if accion not in acciones:
        return redirect('some_nomina')
    try:
        acciones[accion](hora)
        messages.success(request, f'Hora de las {hora.bloque.hora_inicio:%H:%M} actualizada.')
    except TransicionInvalida as error:
        messages.error(request, str(error))
    return redirect(f"{reverse('some_nomina')}?dia={hora.bloque.agenda.fecha.isoformat()}")


@requiere_some
def some_no_vigentes(request):
    """B-19: pacientes que dejaron FONASA. El SOME puede reactivarlos si vuelven a FONASA."""
    if request.method == 'POST':
        paciente = get_object_or_404(Paciente, pk=request.POST.get('paciente'),
                                     estado_inscripcion=Paciente.Estado.NO_VIGENTE)
        if prevision.reactivar(paciente):
            messages.success(request, f'{paciente.usuario.get_full_name()} volvió a FONASA: quedó vigente y ya puede pedir horas.')
        else:
            messages.error(request, f'{paciente.usuario.get_full_name()} sigue con {paciente.get_prevision_display()}: no se puede reactivar.')
        return redirect('some_no_vigentes')
    pacientes = (Paciente.objects.filter(estado_inscripcion=Paciente.Estado.NO_VIGENTE)
                 .select_related('usuario', 'sector').order_by('usuario__last_name'))
    # El motivo va cifrado (no se puede filtrar); las cancelaciones por RN-16 son las que generaron un aviso
    from notificacionesApp.models import RegistroNotificacion
    filas = [{'paciente': p, 'canceladas': RegistroNotificacion.objects.filter(hora__paciente=p).count()}
             for p in pacientes]
    return render(request, 'agendaApp/some_no_vigentes.html', {'filas': filas})
