"""B-14 y B-23: tareas automáticas (lista de espera + recordatorios del día anterior).

Uso:  python manage.py tareas_horasalud            (una vez)
      python manage.py tareas_horasalud --cada 60  (sin parar, cada 60 segundos)
"""
import time

from django.core.management.base import BaseCommand

from proyectoHoraSalud.tareas import ejecutar


class Command(BaseCommand):
    help = 'Vence ofertas de la lista de espera y envía los recordatorios de mañana.'

    def add_arguments(self, parser):
        parser.add_argument('--cada', type=int, default=0, help='Segundos entre revisiones (0 = una sola vez).')

    def handle(self, *args, cada=0, **options):
        while True:
            r = ejecutar()
            espera = r.get('lista_espera') or {}
            self.stdout.write(f"Lista de espera: {espera.get('vencidas', 0)} vencidas, "
                              f"{espera.get('ofertas_nuevas', 0)} avisos · recordatorios enviados: "
                              f"{r.get('recordatorios') or 0}")
            if not cada:
                break
            time.sleep(cada)
