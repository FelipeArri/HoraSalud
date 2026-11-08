"""B-14: vence ofertas sin respuesta y ofrece los cupos al siguiente de la fila.

Uso:  python manage.py procesar_lista_espera            (una vez)
      python manage.py procesar_lista_espera --cada 60  (sin parar, cada 60 segundos)
"""
import time

from django.core.management.base import BaseCommand

from listaEsperaApp.servicios import procesar


class Command(BaseCommand):
    help = 'Revisa la lista de espera: vence ofertas y avisa al siguiente (RF-06).'

    def add_arguments(self, parser):
        parser.add_argument('--cada', type=int, default=0, help='Segundos entre revisiones (0 = una sola vez).')

    def handle(self, *args, cada=0, **options):
        while True:
            resultado = procesar()
            self.stdout.write(f"Ofertas vencidas: {resultado['vencidas']} · avisos nuevos: {resultado['ofertas_nuevas']}")
            if not cada:
                break
            time.sleep(cada)
