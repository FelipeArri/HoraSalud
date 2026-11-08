"""Registro de notificaciones y suscripciones a avisos push (D22-C03). RF-06, B-14."""
from django.db import models

from agendaApp.models import Hora
from autenticacionApp.models import Paciente, Usuario


class RegistroNotificacion(models.Model):
    class Canal(models.TextChoices):
        # B-14: solo canales gratuitos (sin SMS ni correo: tendrían costo para el CESFAM)
        PUSH = 'push', 'Aviso push al teléfono'
        APP = 'app', 'Aviso dentro de HoraSalud'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ENVIADA = 'enviada', 'Enviada'
        FALLIDA = 'fallida', 'Fallida'

    hora = models.ForeignKey(Hora, on_delete=models.SET_NULL, null=True, blank=True)
    # B-14: avisos que no son de una hora existente (por ejemplo, un cupo ofrecido)
    paciente = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    canal = models.CharField(max_length=10, choices=Canal.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    mensaje = models.CharField(max_length=200, blank=True)  # sin datos de salud (Ley 19.628)
    enviado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'notificacion'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.get_canal_display()} - {self.get_estado_display()}'


class SuscripcionPush(models.Model):
    """
    B-14: un telefono o computador que acepto recibir avisos de HoraSalud (Web Push).
    Solo guarda la direccion que entrega el navegador y sus claves publicas: ningun
    dato de salud. Si el navegador la da de baja (respuesta 404/410), se borra.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='suscripciones_push')
    endpoint = models.CharField(max_length=700, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    navegador = models.CharField(max_length=150, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'dispositivo con avisos'
        verbose_name_plural = 'Dispositivos con avisos (push)'

    def __str__(self):
        return f'{self.usuario} · {self.navegador[:40]}'
