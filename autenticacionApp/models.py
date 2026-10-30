"""
Modelos de identidad (D22-C03, D21-C03): Usuario, Sector, Paciente y
Profesional. RF-01 y RF-03.
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import normalizar_rut, validar_rut


class Sector(models.Model):
    nombre = models.CharField(max_length=60)
    comuna = models.CharField(max_length=60)

    class Meta:
        verbose_name_plural = 'Sectores'

    def __str__(self):
        return f'{self.nombre} ({self.comuna})'


class Usuario(AbstractUser):
    """Usuario del sistema. Reemplaza al usuario de Django para agregar RUT y tipo."""

    class Tipo(models.TextChoices):
        PACIENTE = 'paciente', 'Paciente'
        TUTOR = 'tutor', 'Tutor'
        ADMINISTRATIVO = 'administrativo', 'Administrativo SOME'
        PROFESIONAL = 'profesional', 'Profesional'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, validators=[validar_rut])
    telefono = models.CharField(max_length=20, blank=True)
    tipo_usuario = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PACIENTE)

    def save(self, *args, **kwargs):
        if self.rut:
            self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f'{nombre} ({self.rut})' if self.rut else nombre


class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name='paciente')
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, null=True, blank=True)
    ficha_clinica_id = models.CharField('ficha clinica', max_length=20, blank=True)
    # RF-03: null si no tiene tutor
    tutor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='dependientes', limit_choices_to={'tipo_usuario': 'tutor'})

    def __str__(self):
        return str(self.usuario)


class Profesional(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name='profesional')
    especialidad = models.ForeignKey('agendaApp.Especialidad', on_delete=models.PROTECT, null=True, blank=True)
    box_atencion = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = 'Profesionales'

    def __str__(self):
        return str(self.usuario)
