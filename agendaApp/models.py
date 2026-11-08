"""
Modelos de agendamiento (D22-C03, D21-C03): Especialidad, Agenda,
BloqueHorario y Hora. RF-02, RF-05, RN-01, RN-02.
"""
import uuid

from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from autenticacionApp.models import Paciente, Profesional
from proyectoHoraSalud.cifrado import CampoCifrado


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
        EN_OFERTA = 'en_oferta', 'Ofrecido a la lista de espera'  # B-14: retenido mientras se ofrece

    class TipoCupo(models.TextChoices):
        # B-21 (P-07): solo los "programados" se ven en la app del paciente
        PROGRAMADO = 'programado', 'Programado (app)'
        MORBILIDAD = 'morbilidad', 'Morbilidad del día (ventanilla)'
        SOBRECUPO = 'sobrecupo', 'Sobrecupo (ventanilla)'
        # B-14 (RN-17): hora cancelada con menos de 24 h de aviso; ya no se ve en la app
        LIBERADO = 'liberado', 'Cupo liberado (ventanilla)'

    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE, related_name='bloques')
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    tipo_cupo = models.CharField('tipo de cupo', max_length=12, choices=TipoCupo.choices,
                                 default=TipoCupo.PROGRAMADO)

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
        SUSPENDIDA = 'suspendida', 'Suspendida por el CESFAM'  # B-21: profesional ausente

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bloque = models.ForeignKey(BloqueHorario, on_delete=models.PROTECT, related_name='horas')
    # RN-01/RN-02: igual al bloque mientras la hora esta vigente; NULL si se cancela.
    # UNIQUE acepta varios NULL, asi que solo puede haber una hora vigente por bloque.
    bloque_activo = models.OneToOneField(BloqueHorario, on_delete=models.PROTECT, null=True, blank=True,
                                         editable=False, related_name='hora_vigente')
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='horas')
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RESERVADA)
    ESTADOS_SIN_BLOQUE = (Estado.CANCELADA, Estado.SUSPENDIDA)  # dejan de ocupar el bloque
    motivo_cancelacion = CampoCifrado(blank=True, largo_maximo=200)  # cifrado en reposo (B-07)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bloque__agenda__fecha', 'bloque__hora_inicio']

    def save(self, *args, **kwargs):
        # Si la hora ya existia, recordar su bloque anterior (puede haberse movido de bloque).
        bloque_anterior_id = None
        if not self._state.adding:
            bloque_anterior_id = Hora.objects.filter(pk=self.pk).values_list('bloque_id', flat=True).first()

        self.bloque_activo = None if self.estado in self.ESTADOS_SIN_BLOQUE else self.bloque
        with transaction.atomic():
            super().save(*args, **kwargs)
            sincronizar_estado_bloques({self.bloque_id, bloque_anterior_id})
        self.bloque.refresh_from_db(fields=['estado'])

    def __str__(self):
        return f'{self.paciente} - {self.bloque} - {self.get_estado_display()}'

    @property
    def codigo_turno(self):
        """Codigo para la pantalla de sala, sin datos personales (RN-12). Ej.: MG-0820."""
        nombre = self.bloque.agenda.especialidad.nombre.replace('-', ' ')
        sigla = ''.join(p[0] for p in nombre.split() if p[0].isupper())[:2] or 'AT'
        return f'{sigla.upper()}-{self.bloque.hora_inicio:%H%M}'


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


# ---------- B-21 · Gestión de agendas (la carga la Dirección: P-06/P-07) ----------

class PlantillaAgenda(models.Model):
    """Horario semanal de un profesional. Ej.: Dra. Rojas, lunes 08:00-12:00, bloques de 20 min."""

    class Dia(models.IntegerChoices):
        LUNES = 0, 'Lunes'
        MARTES = 1, 'Martes'
        MIERCOLES = 2, 'Miércoles'
        JUEVES = 3, 'Jueves'
        VIERNES = 4, 'Viernes'
        SABADO = 5, 'Sábado'

    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='plantillas')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    dia_semana = models.PositiveSmallIntegerField('día', choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    duracion_min = models.PositiveSmallIntegerField('minutos por bloque', default=20)
    tipo_cupo = models.CharField('tipo de cupo', max_length=12, choices=BloqueHorario.TipoCupo.choices[:2],
                                 default=BloqueHorario.TipoCupo.PROGRAMADO)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'plantilla de agenda'
        verbose_name_plural = 'Plantillas de agenda'
        ordering = ['profesional', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return (f'{self.profesional} · {self.get_dia_semana_display()} '
                f'{self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M} ({self.duracion_min} min)')


class AusenciaProfesional(models.Model):
    """Días en que el profesional no atiende: sus bloques se bloquean y sus horas se suspenden."""

    class Motivo(models.TextChoices):
        LICENCIA = 'licencia', 'Licencia médica'
        VACACIONES = 'vacaciones', 'Vacaciones / feriado legal'
        CAPACITACION = 'capacitacion', 'Capacitación'
        IMPREVISTA = 'imprevista', 'Ausencia imprevista del día'
        OTRO = 'otro', 'Otro'

    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='ausencias')
    desde = models.DateField()
    hasta = models.DateField()
    motivo = models.CharField(max_length=15, choices=Motivo.choices)
    detalle = models.CharField(max_length=150, blank=True)
    registrada_por = models.ForeignKey('autenticacionApp.Usuario', on_delete=models.SET_NULL, null=True,
                                       related_name='+')
    registrada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ausencia de profesional'
        verbose_name_plural = 'Ausencias de profesionales'
        ordering = ['-desde']

    def __str__(self):
        return f'{self.profesional} · {self.desde:%d-%m-%Y} a {self.hasta:%d-%m-%Y} · {self.get_motivo_display()}'


class IndicacionControl(models.Model):
    """P-10: el profesional indica "vuelva en ~1 mes" y el paciente pide la hora después por la app."""
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='indicaciones_control')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    fecha_sugerida = models.DateField()
    indicada_por = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, related_name='+')
    creada_en = models.DateTimeField(auto_now_add=True)
    resuelta_en = models.DateTimeField(null=True, blank=True)  # cuando el paciente reserva

    class Meta:
        verbose_name = 'indicación de control'
        verbose_name_plural = 'Indicaciones de control'
        ordering = ['fecha_sugerida']

    def __str__(self):
        return f'{self.paciente} · {self.especialidad} · desde {self.fecha_sugerida:%d-%m-%Y}'
