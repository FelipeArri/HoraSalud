"""
B-19 · RN-16: revision mensual de la prevision (como el corte mensual de FONASA).

Uso:
    python manage.py revisar_prevision

Consulta FONASA para todos los pacientes vigentes. Quien ya no tenga FONASA queda
"No vigente" y sus horas futuras se cancelan. En produccion se programaria una vez al mes.
"""
from django.core.management.base import BaseCommand

from agendaApp import prevision
from autenticacionApp.models import Paciente


class Command(BaseCommand):
    help = 'Revisa la prevision de todos los pacientes vigentes (RN-16).'

    def handle(self, *args, **opciones):
        revisados, cambios, canceladas = 0, 0, 0
        for paciente in Paciente.objects.filter(estado_inscripcion=Paciente.Estado.VIGENTE).select_related('usuario'):
            resultado = prevision.revalidar(paciente, forzar=True)
            revisados += 1
            if resultado.cambio_a_no_vigente:
                cambios += 1
                canceladas += resultado.horas_canceladas
                self.stdout.write(f'  {paciente.usuario.rut} {paciente.usuario.get_full_name()}: '
                                  f'pasa a {paciente.get_prevision_display()}, queda No vigente y se cancelan {resultado.horas_canceladas} hora(s)')
        self.stdout.write(self.style.SUCCESS(
            f'Revisados: {revisados} | Pasaron a No vigente: {cambios} | Horas canceladas: {canceladas}'))
