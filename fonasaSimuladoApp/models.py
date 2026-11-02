"""
FONASA SIMULADO (sistema externo) · SOLO DATOS FICTICIOS.

Vive en su PROPIA base de datos (fonasa_simulado), separada de horasalud_db,
porque representa a una institucion distinta. HoraSalud solo la CONSULTA a
traves del patron Adapter (autenticacionApp/adapter_inscripcion.py).

Contiene lo que el CESFAM consulta "afuera" al inscribir a alguien:
- prevision y tramo (FONASA, ISAPRE, DIPRECA, CAPREDENA o sin prevision);
- en que establecimiento esta inscrita la persona (inscripcion per capita) y su sector.
"""
from django.core.exceptions import ValidationError
from django.db import models

from autenticacionApp.validators import normalizar_rut, validar_rut

CESFAM = 'CESFAM Padre Esteban Gumucio'


class PersonaFonasa(models.Model):
    class Prevision(models.TextChoices):
        FONASA = 'FONASA', 'FONASA'
        ISAPRE = 'ISAPRE', 'ISAPRE'
        DIPRECA = 'DIPRECA', 'DIPRECA'
        CAPREDENA = 'CAPREDENA', 'CAPREDENA'
        SIN_PREVISION = 'SIN_PREVISION', 'Sin previsión'

    class Inscripcion(models.TextChoices):
        ACTIVA = 'ACTIVA', 'Activa'
        PASIVA = 'PASIVA', 'Pasiva (se trasladó)'
        NO_INSCRITO = 'NO_INSCRITO', 'No inscrito'

    class Sector(models.TextChoices):
        S1 = 'SECTOR 1', 'Sector 1'
        S2 = 'SECTOR 2', 'Sector 2'
        S3 = 'SECTOR 3', 'Sector 3'

    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut],
                           help_text='Con guion y dígito verificador, ej. 31000008-6')
    nombres = models.CharField(max_length=80)
    apellido_paterno = models.CharField(max_length=60)
    apellido_materno = models.CharField(max_length=60, blank=True)
    prevision = models.CharField('previsión', max_length=15, choices=Prevision.choices, default=Prevision.FONASA)
    tramo = models.CharField('tramo FONASA', max_length=1, blank=True,
                             choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    establecimiento = models.CharField('establecimiento de inscripción', max_length=80, default=CESFAM)
    estado_inscripcion = models.CharField('inscripción', max_length=12, choices=Inscripcion.choices,
                                          default=Inscripcion.ACTIVA)
    sector = models.CharField(max_length=10, choices=Sector.choices, blank=True)
    telefono = models.CharField('teléfono', max_length=20, blank=True)
    caso = models.CharField('caso de prueba', max_length=200, blank=True,
                            help_text='Qué situación representa esta persona en las pruebas')

    class Meta:
        verbose_name = 'persona (FONASA simulado)'
        verbose_name_plural = 'Padrón FONASA simulado'
        ordering = ['rut']

    def clean(self):
        if self.prevision == self.Prevision.FONASA and not self.tramo:
            raise ValidationError({'tramo': 'Una persona con FONASA debe tener tramo (A, B, C o D).'})
        if self.prevision != self.Prevision.FONASA:
            self.tramo = ''

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return ' '.join(p for p in [self.nombres, self.apellido_paterno, self.apellido_materno] if p)

    def __str__(self):
        return f'{self.rut} · {self.nombre_completo}'
