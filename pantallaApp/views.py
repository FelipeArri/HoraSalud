from django.shortcuts import render
from django.utils import timezone

from agendaApp.models import Hora


def inicio(request):
    """Pagina de inicio de HoraSalud."""
    return render(request, 'pantallaApp/inicio.html')


def sala_espera(request):
    """
    Pantalla del CESFAM (B-13). Es publica, por eso NO muestra nombres ni RUT
    (RN-10, RN-12): solo un codigo de turno, la hora y el box.
    """
    ahora = timezone.localtime()
    horas = (Hora.objects.filter(bloque__agenda__fecha=ahora.date(),
                                 estado__in=[Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA])
             .select_related('bloque__agenda__especialidad', 'bloque__agenda__profesional')
             .order_by('bloque__hora_inicio'))
    turnos = [{
        'codigo': h.codigo_turno,
        'hora': h.bloque.hora_inicio,
        'especialidad': h.bloque.agenda.especialidad.nombre,
        'box': h.bloque.agenda.profesional.box_atencion or '—',
        'pasada': h.bloque.hora_inicio < ahora.time(),
    } for h in horas]
    proximos = [t for t in turnos if not t['pasada']]
    return render(request, 'pantallaApp/sala_espera.html', {
        'actual': proximos[0] if proximos else None,
        'siguientes': proximos[1:7],
        'ahora': ahora,
    })
