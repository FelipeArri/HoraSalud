"""
B-21 · Pantallas de gestión de agendas.

- Calendario semanal: Administrador CESFAM, SOME y el propio profesional.
- Administrador CESFAM (Dirección): plantilla semanal, generar agendas, duplicar semana, ausencias.
- SOME: ventanilla (morbilidad del día y sobrecupos).
- Profesional: agendar o indicar el próximo control.
"""
from collections import OrderedDict
from datetime import datetime, timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from autenticacionApp.forms import IngresoRutForm
from autenticacionApp.models import Paciente, Profesional
from autenticacionApp.sesion import (_exigir, es_admin_cesfam, es_profesional, es_some, requiere_administrador,
                                     requiere_profesional, requiere_some)

from . import gestion_agendas as ga
from .forms import AusenciaForm, PlantillaForm
from .models import Agenda, AusenciaProfesional, BloqueHorario, Hora, PlantillaAgenda
from .servicios import ReglaNegocioError

requiere_personal_agenda = _exigir(lambda u: es_some(u) or es_admin_cesfam(u) or es_profesional(u),
                                   'Esta sección es solo para el personal del CESFAM.', 'personal_ingresar')


def _profesionales():
    return (Profesional.objects.filter(usuario__is_active=True)
            .select_related('usuario', 'especialidad').order_by('usuario__last_name'))


# ---------- Calendario semanal ----------

@requiere_personal_agenda
def semana(request):
    if es_profesional(request.user):
        profesional = request.user.profesional  # el profesional solo ve su propia agenda
    else:
        profesional = _profesionales().filter(pk=request.GET.get('profesional')).first() or _profesionales().first()
    lunes = ga.lunes_de(ga.fecha_o_hoy(request.GET.get('semana')))
    return render(request, 'agendaApp/agendas_semana.html', {
        'profesional': profesional, 'profesionales': _profesionales(),
        'columnas': ga.semana(profesional, lunes) if profesional else [],
        'lunes': lunes, 'anterior': lunes - timedelta(days=7), 'siguiente': lunes + timedelta(days=7),
        'hoy': timezone.localdate(),
    })


# ---------- Administrador CESFAM (Dirección) ----------

@requiere_administrador
def plantillas(request, profesional_id):
    profesional = get_object_or_404(_profesionales(), pk=profesional_id)
    form = PlantillaForm(request.POST or None, initial={'especialidad': profesional.especialidad})
    if request.method == 'POST' and form.is_valid():
        plantilla = form.save(commit=False)
        plantilla.profesional = profesional
        try:
            ga.validar_plantilla(plantilla)
        except ReglaNegocioError as error:
            form.add_error(None, str(error))
        else:
            plantilla.save()
            messages.success(request, f'Horario agregado: {plantilla}. Ahora presiona "Generar agendas".')
            return redirect('agendas_plantillas', profesional_id=profesional.pk)
    return render(request, 'agendaApp/agendas_plantillas.html', {
        'profesional': profesional, 'form': form,
        'plantillas': PlantillaAgenda.objects.filter(profesional=profesional).select_related('especialidad'),
    })


@require_POST
@requiere_administrador
def plantilla_estado(request, plantilla_id):
    plantilla = get_object_or_404(PlantillaAgenda, pk=plantilla_id)
    plantilla.activa = not plantilla.activa
    if plantilla.activa:
        try:
            ga.validar_plantilla(plantilla)
        except ReglaNegocioError as error:
            messages.error(request, str(error))
            return redirect('agendas_plantillas', profesional_id=plantilla.profesional_id)
    plantilla.save(update_fields=['activa'])
    messages.info(request, 'Los bloques ya generados no cambian; solo afecta a las próximas generaciones.')
    return redirect('agendas_plantillas', profesional_id=plantilla.profesional_id)


@require_POST
@requiere_administrador
def generar(request):
    semanas = max(1, min(int(request.POST.get('semanas') or 4), 8))
    profesional = _profesionales().filter(pk=request.POST.get('profesional')).first()
    creados = ga.generar_agendas(semanas=semanas, profesional=profesional, request=request)
    messages.success(request, f'Se crearon {creados} bloques nuevos para las próximas {semanas} semana(s). '
                              'Lo que ya existía no se tocó.')
    destino = f'?profesional={profesional.pk}' if profesional else ''
    return redirect(f'{reverse("agendas_semana")}{destino}')


@require_POST
@requiere_administrador
def duplicar(request):
    profesional = get_object_or_404(_profesionales(), pk=request.POST.get('profesional'))
    lunes = ga.lunes_de(ga.fecha_o_hoy(request.POST.get('semana')))
    creados = ga.duplicar_semana_anterior(profesional, lunes, request=request)
    messages.success(request, f'Se copiaron {creados} bloques desde la semana anterior.' if creados else
                     'No había bloques nuevos que copiar (la semana anterior está vacía o ya estaba copiada).')
    return redirect(f'{reverse("agendas_semana")}?profesional={profesional.pk}&semana={lunes:%Y-%m-%d}')


@requiere_administrador
def ausencias(request):
    form = AusenciaForm(request.POST or None, initial={
        'profesional': request.GET.get('profesional'), 'desde': timezone.localdate(), 'hasta': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        datos = form.cleaned_data
        resultado = ga.registrar_ausencia(datos['profesional'], datos['desde'], datos['hasta'], datos['motivo'],
                                          datos['detalle'], request=request)
        messages.success(request, f'Ausencia registrada: {resultado.bloques_bloqueados} bloques bloqueados y '
                                  f'{resultado.horas_suspendidas} hora(s) suspendida(s). Los pacientes ven el aviso '
                                  'en la app y quedan primeros en la lista de espera.')
        return redirect('agendas_ausencias')
    return render(request, 'agendaApp/agendas_ausencias.html', {
        'form': form,
        'recientes': AusenciaProfesional.objects.select_related('profesional__usuario', 'registrada_por')[:20],
    })


# ---------- SOME: ventanilla ----------

@requiere_some
def ventanilla(request):
    """Morbilidad del día y sobrecupos: el paciente está presente en el SOME."""
    rut_form = IngresoRutForm(request.GET or None)
    paciente = None
    if request.GET.get('rut') and rut_form.is_valid():
        paciente = (Paciente.objects.select_related('usuario')
                    .filter(usuario__rut=rut_form.cleaned_data['rut']).first())
        if paciente is None:
            rut_form.add_error('rut', 'Ese RUT no está inscrito en HoraSalud. Primero entrégale su código '
                                      '(Activar huella), que valida FONASA y la inscripción.')
    fecha = ga.fecha_o_hoy(request.GET.get('fecha'))
    profesional = _profesionales().filter(pk=request.GET.get('profesional')).first()
    agendas = Agenda.objects.filter(fecha=fecha).select_related('profesional__usuario', 'especialidad')
    if profesional:
        agendas = agendas.filter(profesional=profesional)
    libres = OrderedDict()
    for agenda in agendas.order_by('profesional__usuario__last_name'):
        bloques = [b for b in agenda.bloques.filter(estado=BloqueHorario.Estado.DISPONIBLE)
                   if fecha > timezone.localdate() or b.hora_inicio > timezone.localtime().time()]
        libres[agenda] = {'bloques': bloques, 'sugerida': ga.hora_sugerida_sobrecupo(agenda),
                          'ausente': ga.esta_ausente(agenda.profesional, fecha)}

    if request.method == 'POST' and paciente:
        try:
            if request.POST.get('bloque'):
                hora = ga.dar_hora_ventanilla(paciente, request.POST['bloque'], request=request)
            else:
                agenda = get_object_or_404(Agenda, pk=request.POST.get('agenda'))
                inicio = datetime.strptime(request.POST.get('hora_inicio', ''), '%H:%M').time()
                hora = ga.dar_sobrecupo(paciente, agenda, inicio, request=request)
        except (ReglaNegocioError, ValueError) as error:
            messages.error(request, str(error) if isinstance(error, ReglaNegocioError) else 'Revisa la hora.')
        else:
            messages.success(request, f'Hora entregada a {paciente.usuario.get_full_name()}: '
                                      f'{hora.bloque.agenda.fecha:%d-%m} a las {hora.bloque.hora_inicio:%H:%M} '
                                      f'con {hora.bloque.agenda.profesional} ({hora.bloque.get_tipo_cupo_display()}).')
            return redirect('some_nomina')
        return redirect(request.get_full_path())

    return render(request, 'agendaApp/some_ventanilla.html', {
        'rut_form': rut_form, 'paciente': paciente, 'fecha': fecha, 'profesional': profesional,
        'profesionales': _profesionales(), 'libres': libres,
    })


# ---------- Profesional: próximo control (P-10) ----------

@requiere_profesional
def proximo_control(request, hora_id):
    hora = get_object_or_404(Hora.objects.select_related('paciente__usuario', 'bloque__agenda__especialidad'),
                             pk=hora_id, bloque__agenda__profesional__usuario=request.user)
    if request.method == 'POST':
        try:
            if request.POST.get('accion') == 'indicar':
                semanas = max(1, min(int(request.POST.get('semanas') or 4), 26))
                ga.indicar_control(hora, semanas, request=request)
                messages.success(request, f'Indicado: {hora.paciente.usuario.get_full_name()} verá en la app el '
                                          f'recordatorio para pedir su control en {semanas} semana(s).')
            else:
                nueva = ga.agendar_proximo_control(hora, request.POST.get('bloque'), request=request)
                messages.success(request, f'Control agendado para el {nueva.bloque.agenda.fecha:%d-%m-%Y} a las '
                                          f'{nueva.bloque.hora_inicio:%H:%M}.')
        except (ReglaNegocioError, BloqueHorario.DoesNotExist, ValueError) as error:
            messages.error(request, str(error) if isinstance(error, ReglaNegocioError) else 'Elige un horario.')
            return redirect('profesional_control', hora_id=hora.pk)
        return redirect('profesional_agenda')
    sugerida = timezone.localdate() + timedelta(weeks=4)
    dias = OrderedDict()
    for bloque in ga.bloques_para_control(request.user.profesional):
        dias.setdefault(bloque.agenda.fecha, []).append(bloque)
    return render(request, 'agendaApp/profesional_control.html', {
        'hora': hora, 'dias': dias, 'sugerida': sugerida})
