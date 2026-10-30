"""Registro de notificaciones enviadas (D22-C03). RF-06."""
from django.db import models

from agendaApp.models import Hora


class RegistroNotificacion(models.Model):
    class Canal(models.TextChoices):
        SMS = 'sms', 'SMS'
        EMAIL = 'email', 'Correo'
        APP = 'app', 'Aplicacion'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ENVIADA = 'enviada', 'Enviada'
        FALLIDA = 'fallida', 'Fallida'

    hora = models.ForeignKey(Hora, on_delete=models.SET_NULL, null=True, blank=True)
    canal = models.CharField(max_length=10, choices=Canal.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    enviado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'notificacion'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.get_canal_display()} - {self.get_estado_display()}'
