"""
Deja HoraSalud SIN pacientes ni tutores, para probar desde cero (solo datos de prueba).

Uso:
    python manage.py vaciar_pacientes --confirmar

Borra pacientes, tutores, sus horas, lista de espera, huellas, consentimientos y
codigos de enrolamiento. NO toca funcionarios, profesionales, agendas ni el padron
FONASA simulado. Despues, los pacientes entran solo por el flujo real: el SOME consulta
el padron, entrega el codigo y la persona activa su huella.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agendaApp.models import Hora
from autenticacionApp.models import Paciente, Usuario
from listaEsperaApp.models import EsperaPaciente


@transaction.atomic
def vaciar():
    personas = Usuario.objects.filter(tipo_usuario__in=[Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR])
    horas = Hora.objects.filter(paciente__usuario__in=personas)
    total_horas = horas.count()
    EsperaPaciente.objects.filter(paciente__usuario__in=personas).delete()
    for hora in horas:  # una por una, para que cada bloque vuelva a quedar libre (DEF-01)
        hora.delete()
    Paciente.objects.filter(usuario__in=personas).delete()
    total = personas.count()
    personas.delete()  # en cascada: huellas, consentimientos, codigos y solicitudes
    return total, total_horas


class Command(BaseCommand):
    help = 'Borra todos los pacientes y tutores para probar desde cero (requiere --confirmar).'

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true', help='Confirma que quieres borrar.')

    def handle(self, *args, confirmar=False, **opciones):
        if not confirmar:
            raise CommandError('Esto borra TODOS los pacientes y tutores. Repite con --confirmar.')
        personas, horas = vaciar()
        self.stdout.write(self.style.SUCCESS(
            f'Listo: se borraron {personas} pacientes/tutores y {horas} horas. '
            'Funcionarios, agendas y padrón FONASA quedaron intactos.'))
