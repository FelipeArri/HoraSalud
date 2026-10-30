"""Modelo de la lista de espera (D22-C03). RF-06."""
from django.db import models

from agendaApp.models import Especialidad
from autenticacionApp.models import Paciente


class EsperaPaciente(models.Model):
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'paciente en espera'
        verbose_name_plural = 'Lista de espera'
        ordering = ['especialidad', 'orden']
        indexes = [models.Index(fields=['especialidad', 'orden'])]

    def __str__(self):
        return f'{self.orden}. {self.paciente} ({self.especialidad})'
