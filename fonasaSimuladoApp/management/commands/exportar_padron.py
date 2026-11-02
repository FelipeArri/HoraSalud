"""
Genera un Excel de CONSULTA con el padrón FONASA simulado (todas las personas ficticias).

Uso:
    python manage.py exportar_padron

Crea reportes/padron_fonasa_simulado.xlsx (fuera de Git). Para AGREGAR o EDITAR
personas se usa /admin/ → "Padrón FONASA simulado"; el Excel es solo para leer.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from autenticacionApp.models import Usuario
from fonasaSimuladoApp.models import CESFAM, PersonaFonasa
from proyectoHoraSalud.excel import guardar_excel


class Command(BaseCommand):
    help = 'Exporta el padrón FONASA simulado a reportes/padron_fonasa_simulado.xlsx.'

    def handle(self, *args, **opciones):
        en_app = set(Usuario.objects.exclude(rut=None).values_list('rut', flat=True))
        filas = []
        for p in PersonaFonasa.objects.all():
            puede = (p.prevision == 'FONASA' and p.estado_inscripcion == 'ACTIVA' and p.establecimiento == CESFAM)
            filas.append([p.rut, p.nombre_completo, p.get_prevision_display(), p.tramo or '—',
                          p.get_estado_inscripcion_display(), p.establecimiento, p.get_sector_display() or '—',
                          'Sí' if puede else 'No', 'Sí' if p.rut in en_app else 'No', p.caso])
        destino = guardar_excel(
            'padron_fonasa_simulado.xlsx', 'Padrón FONASA simulado',
            f'Sistema externo simulado · solo datos ficticios · generado el {timezone.localtime():%d-%m-%Y %H:%M}',
            ['RUT', 'Nombre', 'Previsión', 'Tramo', 'Inscripción', 'Establecimiento', 'Sector',
             '¿Puede recibir código?', '¿Ya está en HoraSalud?', 'Caso de prueba'],
            filas, [13, 28, 14, 7, 18, 28, 10, 12, 12, 50])
        self.stdout.write(self.style.SUCCESS(f'{len(filas)} personas exportadas a {destino}'))
