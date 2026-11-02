"""
B-19 · RN-16: prevision vigente.

Si un paciente inscrito deja FONASA (pasa a ISAPRE, DIPRECA o CAPREDENA, o queda
sin prevision) deja de pertenecer al consultorio (respuesta del CESFAM, P-05 y P-08):
1. queda "No vigente";
2. sus horas FUTURAS se cancelan con motivo "CESFAM: cambio de prevision" (RN-05)
   y los bloques quedan libres para otras personas;
3. se registra un aviso para el paciente (RN-13);
4. ya no puede pedir horas por la app.
Si vuelve a FONASA, lo reactiva el SOME en ventanilla.

Cuando se revisa:
- al pedir una hora, si la ultima consulta tiene mas de 30 dias;
- una vez al mes, con el comando `python manage.py revisar_prevision`.
"""
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from autenticacionApp.adapter_inscripcion import PrevisionService, servicios_externos
from autenticacionApp.models import Paciente
from notificacionesApp.models import RegistroNotificacion

from .models import Hora

VIGENCIA_CONSULTA = timedelta(days=30)
NOMBRES = dict(Paciente.Prevision.choices)


@dataclass
class Resultado:
    consultado: bool          # si se llamó a FONASA
    cambio_a_no_vigente: bool = False
    horas_canceladas: int = 0


def consulta_vencida(paciente):
    return (paciente.prevision_consultada_en is None
            or timezone.now() - paciente.prevision_consultada_en > VIGENCIA_CONSULTA)


def horas_futuras(paciente):
    hoy = timezone.localdate()
    return (Hora.objects.filter(paciente=paciente, bloque__agenda__fecha__gte=hoy,
                                estado__in=[Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA])
            .select_related('bloque__agenda'))


@transaction.atomic
def dejar_no_vigente(paciente, prevision):
    """RN-16: aplica el cambio de prevision. Devuelve cuántas horas se cancelaron."""
    paciente.prevision = prevision
    paciente.tramo = ''
    paciente.estado_inscripcion = Paciente.Estado.NO_VIGENTE
    paciente.save(update_fields=['prevision', 'tramo', 'estado_inscripcion'])
    canceladas = 0
    for hora in horas_futuras(paciente):
        hora.estado = Hora.Estado.CANCELADA
        hora.motivo_cancelacion = f'CESFAM: cambio de previsión ({NOMBRES.get(prevision, prevision)})'
        hora.save()  # Hora.save() libera el bloque (DEF-01)
        RegistroNotificacion.objects.create(hora=hora, canal=RegistroNotificacion.Canal.APP)  # aviso RN-13
        canceladas += 1
    return canceladas


def revalidar(paciente, servicios=None, forzar=False):
    """Consulta FONASA si corresponde y aplica RN-16 si el paciente ya no tiene FONASA."""
    if paciente.estado_inscripcion == Paciente.Estado.NO_VIGENTE:
        return Resultado(consultado=False)
    if not forzar and not consulta_vencida(paciente):
        return Resultado(consultado=False)
    _, fonasa = servicios or servicios_externos()
    datos = fonasa.consultar_prevision(paciente.usuario.rut)
    paciente.prevision_consultada_en = timezone.now()
    if datos['prevision'] == PrevisionService.FONASA:
        paciente.tramo = datos['tramo']
        paciente.save(update_fields=['prevision_consultada_en', 'tramo'])
        return Resultado(consultado=True)
    paciente.save(update_fields=['prevision_consultada_en'])
    return Resultado(consultado=True, cambio_a_no_vigente=True,
                     horas_canceladas=dejar_no_vigente(paciente, datos['prevision']))


def reactivar(paciente, servicios=None):
    """El SOME vuelve a consultar FONASA. Solo se reactiva si tiene FONASA vigente."""
    _, fonasa = servicios or servicios_externos()
    datos = fonasa.consultar_prevision(paciente.usuario.rut)
    paciente.prevision_consultada_en = timezone.now()
    paciente.prevision = datos['prevision']
    if datos['prevision'] == PrevisionService.FONASA:
        paciente.tramo = datos['tramo']
        paciente.estado_inscripcion = Paciente.Estado.VIGENTE
    paciente.save(update_fields=['prevision_consultada_en', 'prevision', 'tramo', 'estado_inscripcion'])
    return paciente.estado_inscripcion == Paciente.Estado.VIGENTE


def mensaje_no_vigente(paciente):
    return (f'Tu previsión registrada es {NOMBRES.get(paciente.prevision, paciente.prevision)}: ya no perteneces '
            'a este CESFAM, por eso no puedes pedir horas por la aplicación. Si vuelves a FONASA, acércate al SOME.')
