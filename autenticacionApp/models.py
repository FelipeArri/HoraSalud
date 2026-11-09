"""
Modelos de identidad (D22-C03, D21-C03): Usuario, Sector, Paciente y
Profesional. RF-01 y RF-03.
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from proyectoHoraSalud.cifrado import CampoCifrado

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
        ADMINISTRADOR = 'administrador', 'Administrador CESFAM'  # B-20: Dirección, gestiona al personal

    PERSONAL = (Tipo.ADMINISTRATIVO, Tipo.PROFESIONAL, Tipo.ADMINISTRADOR)  # entran con RUT + clave

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, validators=[validar_rut])
    telefono = CampoCifrado(blank=True, largo_maximo=20)  # cifrado en reposo (B-07)
    tipo_usuario = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PACIENTE)
    # B-20: ingreso del personal con clave (bloqueo por intentos, clave temporal)
    debe_cambiar_clave = models.BooleanField('debe cambiar su clave', default=False)
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    @property
    def es_personal(self):
        return self.tipo_usuario in self.PERSONAL

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

    # B-18 / B-19: datos leidos de FONASA y del sistema clinico (no se guarda el domicilio)
    class Prevision(models.TextChoices):
        FONASA = 'fonasa', 'FONASA'
        ISAPRE = 'isapre', 'ISAPRE'
        DIPRECA = 'dipreca', 'DIPRECA'
        CAPREDENA = 'capredena', 'CAPREDENA'
        SIN_PREVISION = 'sin_prevision', 'Sin previsión'

    class Estado(models.TextChoices):
        VIGENTE = 'vigente', 'Vigente'
        NO_VIGENTE = 'no_vigente', 'No vigente'

    prevision = models.CharField('previsión', max_length=15, choices=Prevision.choices, default=Prevision.FONASA)
    tramo = models.CharField('tramo FONASA', max_length=1, blank=True)
    estado_inscripcion = models.CharField('estado', max_length=10, choices=Estado.choices, default=Estado.VIGENTE)
    prevision_consultada_en = models.DateTimeField('última consulta a FONASA', null=True, blank=True)

    def __str__(self):
        return str(self.usuario)


class Profesional(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name='profesional')
    especialidad = models.ForeignKey('agendaApp.Especialidad', on_delete=models.PROTECT, null=True, blank=True)
    box_atencion = models.CharField(max_length=10, blank=True)
    # DEF-06 (RF-02): sector que atiende. Vacío = atiende a todos los sectores (por ejemplo, los programas).
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, null=True, blank=True,
                               help_text='Déjalo vacío si atiende a pacientes de todos los sectores.')

    class Meta:
        verbose_name_plural = 'Profesionales'

    def __str__(self):
        return str(self.usuario)


class CredencialPasskey(models.Model):
    """
    Passkey de un usuario (B-06, RNF-SEC02). El servidor guarda SOLO la clave
    publica: la huella o el rostro nunca salen del telefono (Ley 21.719).
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='passkeys')
    credencial_id = models.CharField(max_length=255, unique=True)  # base64url
    # Dominio donde se creo (localhost o el de ngrok): una passkey solo sirve en su dominio
    rp_id = models.CharField('dominio', max_length=253, default='localhost')
    clave_publica = models.BinaryField()
    contador_firmas = models.PositiveBigIntegerField(default=0)
    dispositivo = models.CharField(max_length=120, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    ultimo_uso = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'passkey'
        verbose_name_plural = 'Passkeys'

    def __str__(self):
        return f'{self.usuario} - {self.dispositivo or "dispositivo"}'


class CodigoEnrolamiento(models.Model):
    """
    Codigo de un solo uso que entrega el SOME despues de validar la cedula
    EN PERSONA. Se guarda solo su hash; vence y se bloquea tras 5 intentos.
    """
    MAX_INTENTOS = 5

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='codigos_enrolamiento')
    codigo_hash = models.CharField(max_length=64)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='+')
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'código de enrolamiento'
        verbose_name_plural = 'Códigos de enrolamiento'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.usuario} - {"usado" if self.usado_en else "vigente"}'


class Consentimiento(models.Model):
    """
    B-07 · Ley 21.719: registro de que la persona aceptó (o rechazó) la política de
    privacidad de HoraSalud, con su versión y fecha. Si la política cambia de versión,
    se vuelve a pedir. Retirar el consentimiento queda registrado, no se borra.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='consentimientos')
    version = models.CharField('versión de la política', max_length=10)
    aceptado = models.BooleanField()
    fecha = models.DateTimeField(auto_now_add=True)
    retirado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'consentimiento'
        verbose_name_plural = 'Consentimientos'
        ordering = ['-fecha']

    def __str__(self):
        estado = 'retirado' if self.retirado_en else ('aceptado' if self.aceptado else 'rechazado')
        return f'{self.usuario} · v{self.version} · {estado}'


class RegistroAuditoria(models.Model):
    """
    B-20 · RN-11: quién hizo qué y cuándo. Cubre las acciones del personal y, desde
    DEF-07, la reserva, la cancelación y el No-Show. No se edita ni se borra desde la
    app. Guarda el RUT aparte por si la cuenta se desactiva.
    """

    class Accion(models.TextChoices):
        INGRESO = 'ingreso', 'Ingreso al sistema'
        INGRESO_FALLIDO = 'ingreso_fallido', 'Clave incorrecta al ingresar'
        CUENTA_BLOQUEADA = 'cuenta_bloqueada', 'Cuenta bloqueada por intentos'
        CAMBIO_CLAVE = 'cambio_clave', 'Cambió su clave'
        ALTA = 'alta', 'Agregó un funcionario'
        DESACTIVACION = 'desactivacion', 'Desactivó un funcionario'
        REACTIVACION = 'reactivacion', 'Reactivó un funcionario'
        CLAVE_TEMPORAL = 'clave_temporal', 'Entregó clave temporal'
        REAUTENTICACION_FALLIDA = 'reauth_fallida', 'Clave de confirmación incorrecta'
        SESION_CERRADA = 'sesion_cerrada', 'Sesión cerrada por 3 claves incorrectas'
        # B-21 · agendas
        AGENDA = 'agenda', 'Cargó o generó agendas'
        AUSENCIA = 'ausencia', 'Registró ausencia de profesional'
        SOBRECUPO = 'sobrecupo', 'Dio hora en ventanilla / sobrecupo'
        PROXIMO_CONTROL = 'proximo_control', 'Agendó o indicó próximo control'
        # DEF-07 · horas de los pacientes
        RESERVA = 'reserva', 'Reservó una hora'
        CANCELACION = 'cancelacion', 'Canceló una hora'
        NO_SHOW = 'no_show', 'Marcó inasistencia (No-Show)'
        ATENDIDA = 'atendida', 'Marcó hora atendida'
        # DEF-08 · ingreso de pacientes y tutores
        INGRESO_BLOQUEADO = 'ingreso_bloqueado', 'Ingreso bloqueado por intentos'
        # B-10 · vínculo de tutor (RF-03)
        TUTOR_AUTORIZADO = 'tutor_autorizado', 'Autorizó un tutor'
        TUTOR_REVOCADO = 'tutor_revocado', 'Quitó un tutor'
        TUTOR_ACTUA = 'tutor_actua', 'Tutor eligió actuar por un paciente'
        # Trazabilidad de sesiones de todos los roles
        SALIDA = 'salida', 'Cerró sesión'
        # B-14 · lista de espera (RF-06)
        ESPERA_ALTA = 'espera_alta', 'Inscribió en lista de espera'
        ESPERA_BAJA = 'espera_baja', 'Sacó de la lista de espera'
        CUPO_ACEPTADO = 'cupo_aceptado', 'Aceptó un cupo de la lista de espera'
        # CC-19 · segundo factor del personal
        MFA_QUITADO = 'mfa_quitado', 'Quitó los dispositivos de segundo factor'

    fecha = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    actor_rut = models.CharField('RUT de quien actúa', max_length=12, blank=True)
    # Rol al momento del evento (se guarda como texto: si después cambia, el registro no cambia)
    actor_rol = models.CharField('rol de quien actúa', max_length=30, blank=True)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    objetivo = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    objetivo_rut = models.CharField('RUT afectado', max_length=12, blank=True)
    objetivo_rol = models.CharField('rol de la persona afectada', max_length=30, blank=True)
    detalle = models.CharField(max_length=200, blank=True)
    # Frase completa: quién (rol, nombre, RUT), qué hizo, sobre quién y el detalle
    descripcion = models.CharField('descripción', max_length=400, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'registro de auditoría'
        verbose_name_plural = 'Registro de auditoría'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.fecha:%d-%m-%Y %H:%M} · {self.actor_rut} · {self.get_accion_display()}'


class SolicitudDerechos(models.Model):
    """B-07 · Derechos ARCO+ (Ley 21.719): la persona pide rectificar, suprimir, etc. Lo resuelve el SOME."""

    class Tipo(models.TextChoices):
        RECTIFICACION = 'rectificacion', 'Corregir un dato (rectificación)'
        SUPRESION = 'supresion', 'Eliminar mis datos de la app (supresión)'
        OPOSICION = 'oposicion', 'No quiero recibir avisos (oposición)'
        BLOQUEO = 'bloqueo', 'Bloquear temporalmente mis datos (bloqueo)'
        OTRO = 'otro', 'Otra consulta sobre mis datos'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        RESUELTA = 'resuelta', 'Resuelta'

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes_derechos')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    detalle = CampoCifrado(blank=True, largo_maximo=500)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creada_en = models.DateTimeField(auto_now_add=True)
    respuesta = CampoCifrado(blank=True, largo_maximo=500)
    resuelta_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'solicitud de derechos'
        verbose_name_plural = 'Solicitudes de derechos (ARCO+)'
        ordering = ['estado', 'creada_en']

    def __str__(self):
        return f'{self.usuario} · {self.get_tipo_display()} · {self.get_estado_display()}'
