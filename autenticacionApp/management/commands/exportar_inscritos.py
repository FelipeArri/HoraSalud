"""
Genera un Excel de CONSULTA con quién está HOY dentro de HoraSalud (pacientes y tutores).

Uso:
    python manage.py exportar_inscritos

Crea reportes/inscritos_AAAA-MM-DD.xlsx (fuera de Git). Es una "foto" de tu base
horasalud_db en ese momento: la de otro integrante será distinta.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from autenticacionApp import privacidad
from autenticacionApp.models import Usuario
from proyectoHoraSalud.excel import guardar_excel


class Command(BaseCommand):
    help = 'Exporta los pacientes y tutores de HoraSalud a reportes/inscritos_FECHA.xlsx.'

    def handle(self, *args, **opciones):
        personas = (Usuario.objects.filter(tipo_usuario__in=[Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR])
                    .select_related('paciente__sector').order_by('last_name', 'first_name'))
        filas = []
        for u in personas:
            paciente = getattr(u, 'paciente', None)
            filas.append([
                u.rut or '—', u.get_full_name(), u.get_tipo_usuario_display(),
                paciente.sector.nombre if paciente and paciente.sector else '—',
                paciente.get_prevision_display() if paciente else '—',
                paciente.tramo if paciente and paciente.tramo else '—',
                paciente.get_estado_inscripcion_display() if paciente else '—',
                u.passkeys.count(),
                'Sí' if privacidad.consentimiento_vigente(u) else 'No',
                paciente.horas.filter(estado__in=['reservada', 'confirmada']).count() if paciente else 0,
            ])
        hoy = timezone.localdate()
        destino = guardar_excel(
            f'inscritos_{hoy:%Y-%m-%d}.xlsx', 'Inscritos en HoraSalud',
            f'Foto de la base horasalud_db · solo datos ficticios · {timezone.localtime():%d-%m-%Y %H:%M}',
            ['RUT', 'Nombre', 'Tipo', 'Sector', 'Previsión', 'Tramo', 'Estado', 'Dispositivos con huella',
             '¿Aceptó la política?', 'Horas vigentes'],
            filas, [13, 28, 12, 10, 14, 7, 12, 12, 12, 10])
        self.stdout.write(self.style.SUCCESS(f'{len(filas)} personas exportadas a {destino}'))
