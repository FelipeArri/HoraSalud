"""
Patron Observer (D26-C03) con las señales de Django.

agendaApp "publica" que un cupo quedo libre y no sabe quien escucha. La lista
de espera (listaEsperaApp) se suscribe en su apps.py. Asi la Hora no conoce
la logica de la lista ni de las notificaciones (bajo acoplamiento).
"""
from django.dispatch import Signal

# Argumentos: bloque (BloqueHorario que quedó libre) y motivo ('cancelacion').
cupo_liberado = Signal()
