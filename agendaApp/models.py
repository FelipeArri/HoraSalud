"""
Modelos de agendamiento (D22-C03, D21-C03): Especialidad, Agenda,
BloqueHorario y Hora. RF-02, RF-05, RN-01, RN-02.
"""
import uuid

from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from autenticacionApp.models import Paciente, Profesional


class Especialidad(models.Model):
    class Tipo(models.TextChoices):
        MEDICINA_GENERAL = 'medicina_general', 'Medicina general'
        PROGRAMA = 'programa', 'Programa'

    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    class Meta:
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.nombre


class Agenda(models.Model):
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    profesional = models.ForeignKey(Profesional, on_delete=models.PROTECT)
    fecha = models.DateField()

    class Meta:
        indexes = [models.Index(fields=['especialidad', 'fecha'])]

    def __str__(self):
        return f'{self.especialidad} - {self.profesional} - {self.fecha:%d-%m-%Y}'


class BloqueHorario(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        RESERVADO = 'reservado', 'Reservado'
        BLOQUEADO = 'bloqueado', 'Bloqueado'

    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE, related_name='bloques')
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)

    class Meta:
        verbose_name = 'bloque horario'
        verbose_name_plural = 'Bloques horarios'
        constraints = [models.UniqueConstraint(fields=['agenda', 'hora_inicio'], name='uq_bloque_agenda_horario')]
        ordering = ['agenda__fecha', 'hora_inicio']

    def __str__(self):
        return f'{self.agenda.fecha:%d-%m-%Y} {self.hora_inicio:%H:%M} ({self.get_estado_display()})'


class Hora(models.Model):
    """Cita de un paciente en un bloque. Estados segun D12-C03-Dia_Estados_Hora."""

    class Estado(models.TextChoices):
        RESERVADA = 'reservada', 'Reservada'
        CONFIRMADA = 'confirmada', 'Confirmada'
        ATENDIDA = 'atendida', 'Atendida'
        CANCELADA = 'cancelada', 'Cancelada'
        NO_SHOW = 'no_show', 'No-Show'
        REASIGNADA = 'reasignada', 'Reasignada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bloque = models.ForeignKey(BloqueHorario, on_delete=models.PROTECT, related_name='horas')
    # RN-01/RN-02: igual al bloque mientras la hora esta vigente; NULL si se cancela.
    # UNIQUE acepta varios NULL, asi que solo puede haber una hora vigente por bloque.
    bloque_activo = models.OneToOneField(BloqueHorario, on_delete=models.PROTECT, null=True, blank=True,
                                         editable=False, related_name='hora_vigente')
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='horas')
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RESERVADA)
    motivo_cancelacion = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bloque__agenda__fecha', 'bloque__hora_inicio']

    def save(self, *args, **kwargs):
        # Si la hora ya existia, recordar su bloque anterior (puede haberse movido de bloque).
        bloque_anterior_id = None
        if not self._state.adding:
            bloque_anterior_id = Hora.objects.filter(pk=self.pk).values_list('bloque_id', flat=True).first()

        self.bloque_activo = None if self.estado == self.Estado.CANCELADA else self.bloque
        with transaction.atomic():
            super().save(*args, **kwargs)
            sincronizar_estado_bloques({self.bloque_id, bloque_anterior_id})
        self.bloque.refresh_from_db(fields=['estado'])

    def __str__(self):
        return f'{self.paciente} - {self.bloque} - {self.get_estado_display()}'


def sincronizar_estado_bloques(bloque_ids):
    """Defecto DEF-01: el bloque queda 'Reservado' si tiene una hora vigente y
    'Disponible' si no la tiene. Los bloques 'Bloqueado' no se tocan."""
    for bloque_id in bloque_ids - {None}:
        ocupado = Hora.objects.filter(bloque_activo_id=bloque_id).exists()
        nuevo_estado = BloqueHorario.Estado.RESERVADO if ocupado else BloqueHorario.Estado.DISPONIBLE
        (BloqueHorario.objects.filter(pk=bloque_id)
         .exclude(estado=BloqueHorario.Estado.BLOQUEADO)
         .update(estado=nuevo_estado))


@receiver(post_delete, sender=Hora)
def liberar_bloque_al_borrar_hora(sender, instance, **kwargs):
    # Si se borra una hora (por ejemplo desde /admin/), su bloque vuelve a quedar libre.
    sincronizar_estado_bloques({instance.bloque_id})
