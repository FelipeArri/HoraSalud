from django.apps import AppConfig


class ListaesperaappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listaEsperaApp'
    verbose_name = 'Lista de espera'

    def ready(self):
        from . import receptores  # noqa: F401  conecta el Observer (B-14)
