"""
Modelos de la lista de espera (D22-C03). RF-06 y RN-17 (B-14).

- EsperaPaciente: la fila de cada especialidad. El orden se respeta siempre.
- CupoLiberado: cada hora cancelada que entra al proceso, con su anticipacion
  (sirve para las estadisticas que calibran los tramos).
- OfertaCupo: cada vez que el cupo se le ofrece a una persona de la fila.
"""
import uuid

from django.db import models

from agendaApp.models import BloqueHorario, Especialidad
from autenticacionApp.models import Paciente


class EsperaPaciente(models.Model):
    class Origen(models.TextChoices):
        APP = 'app', 'Desde la aplicación'
        SOME = 'some', 'En ventanilla (SOME)'
        CESFAM = 'cesfam', 'Hora suspendida por el CESFAM'

    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='esperas')
    orden = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)
    inscrito_por = models.CharField('inscrito', max_length=10, choices=Origen.choices, default=Origen.APP)
    # Ofertas seguidas que vencieron sin respuesta. No castiga: solo avisa al SOME para llamarlo.
    ofertas_sin_respuesta = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'paciente en espera'
        verbose_name_plural = 'Lista de espera'
        ordering = ['especialidad', 'orden', 'creado_en']
        indexes = [models.Index(fields=['especialidad', 'orden'])]
        constraints = [models.UniqueConstraint(fields=['especialidad', 'paciente'], name='uq_espera_paciente')]

    def __str__(self):
        return f'{self.orden}. {self.paciente} ({self.especialidad})'


class CupoLiberado(models.Model):
    """Una hora cancelada que entra a la lista de espera (o se deriva a ventanilla)."""

    class Resultado(models.TextChoices):
        EN_CURSO = 'en_curso', 'Ofreciéndose a la lista'
        REASIGNADO = 'reasignado', 'Tomado por la lista de espera'
        VENTANILLA = 'ventanilla', 'Pasó a la ventanilla del SOME'
        LIBRE_APP = 'libre_app', 'Nadie lo tomó: quedó libre en la app'

    bloque = models.ForeignKey(BloqueHorario, on_delete=models.CASCADE, related_name='liberaciones')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    liberado_en = models.DateTimeField(auto_now_add=True)
    anticipacion_horas = models.FloatField('horas de anticipación al liberarse')
    resultado = models.CharField(max_length=12, choices=Resultado.choices, default=Resultado.EN_CURSO)
    resuelto_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'cupo liberado'
        verbose_name_plural = 'Cupos liberados'
        ordering = ['-liberado_en']

    def __str__(self):
        return f'{self.bloque} · {self.get_resultado_display()}'


class OfertaCupo(models.Model):
    class Tramo(models.TextChoices):
        LARGO = 'largo', 'Más de 48 h (1 hora para responder)'
        CORTO = 'corto', 'Entre 24 y 48 h (10 minutos para responder)'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Esperando respuesta'
        ACEPTADA = 'aceptada', 'Aceptada'
        RECHAZADA = 'rechazada', 'No puede'
        VENCIDA = 'vencida', 'Venció sin respuesta'
        ANULADA = 'anulada', 'Anulada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cupo = models.ForeignKey(CupoLiberado, on_delete=models.CASCADE, related_name='ofertas')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='ofertas_cupo')
    posicion = models.PositiveIntegerField('lugar en la fila al ofrecerse')
    tramo = models.CharField(max_length=6, choices=Tramo.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    enviada_en = models.DateTimeField()
    vence_en = models.DateTimeField()
    respondida_en = models.DateTimeField(null=True, blank=True)
    respondida_por = models.CharField(max_length=30, blank=True)  # Paciente, Tutor o SOME (por teléfono)

    class Meta:
        verbose_name = 'oferta de cupo'
        verbose_name_plural = 'Ofertas de cupo'
        ordering = ['-enviada_en']
        indexes = [models.Index(fields=['estado', 'vence_en'])]

    def __str__(self):
        return f'{self.paciente} · {self.cupo.bloque} · {self.get_estado_display()}'

    @property
    def bloque(self):
        return self.cupo.bloque
