"""
B-18 · RF-01 · RN-15: antes de entregar el codigo para activar la huella, el SOME
consulta OBLIGATORIAMENTE el sistema clinico del CESFAM y FONASA.

Reglas (respuestas del CESFAM, Trello P-01 a P-08):
- Solo se entrega codigo a quien esta INSCRITO en el CESFAM y tiene FONASA A, B, C o D.
- ISAPRE, DIPRECA o CAPREDENA: no pertenece al consultorio.
- Sin prevision: se orienta a postular a FONASA como carente de recursos.
- El tutor o cuidador no necesita inscripcion ni FONASA (actua por otra persona).
- HoraSalud no guarda el domicilio: solo el sector que informa el sistema clinico.
"""
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from .adapter_inscripcion import PrevisionService, servicios_externos
from .models import CodigoEnrolamiento, Paciente, Sector, Usuario

MENSAJES_RECHAZO = {
    'no_inscrito': 'No está inscrito en el CESFAM. Debe inscribirse primero en el consultorio.',
    PrevisionService.ISAPRE: 'Tiene ISAPRE: no pertenece al consultorio.',
    PrevisionService.DIPRECA: 'Tiene DIPRECA: no pertenece al consultorio.',
    PrevisionService.CAPREDENA: 'Tiene CAPREDENA: no pertenece al consultorio.',
    PrevisionService.SIN_PREVISION: ('No tiene previsión. Orientar a postular a FONASA como carente de recursos; '
                                     'cuando FONASA esté vigente, podrá activar la aplicación.'),
}


@dataclass
class Consulta:
    rut: str
    usuario: Usuario | None = None          # si ya existe en HoraSalud
    es_tutor: bool = False
    inscripcion: dict = field(default_factory=dict)
    prevision: dict = field(default_factory=dict)
    motivo_rechazo: str = ''

    @property
    def puede_recibir_codigo(self):
        return not self.motivo_rechazo

    @property
    def nombre(self):
        if self.usuario:
            return self.usuario.get_full_name()
        return f"{self.inscripcion.get('nombres', '')} {self.inscripcion.get('apellidos', '')}".strip()

    @property
    def tramo_texto(self):
        if self.prevision.get('prevision') == PrevisionService.FONASA:
            return f"FONASA tramo {self.prevision.get('tramo') or '?'}"
        return dict(Paciente.Prevision.choices).get(self.prevision.get('prevision'), '—')

    @property
    def dispositivos(self):
        return self.usuario.passkeys.count() if self.usuario else 0

    @property
    def codigo_vigente(self):
        if not self.usuario:
            return None
        return (CodigoEnrolamiento.objects.filter(usuario=self.usuario, usado_en__isnull=True,
                                                  expira_en__gt=timezone.now()).first())


def consultar(rut, servicios=None):
    """Consulta el sistema clinico y FONASA. No guarda nada."""
    clinico, fonasa = servicios or servicios_externos()
    usuario = Usuario.objects.filter(rut=rut, is_active=True,
                                     tipo_usuario__in=[Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR]).first()
    consulta = Consulta(rut=rut, usuario=usuario)
    if usuario and usuario.tipo_usuario == Usuario.Tipo.TUTOR:
        consulta.es_tutor = True  # actua por otra persona: no requiere inscripcion ni FONASA
        return consulta
    consulta.inscripcion = clinico.consultar_inscripcion(rut)
    if not consulta.inscripcion['inscrito']:
        consulta.motivo_rechazo = MENSAJES_RECHAZO['no_inscrito']
        return consulta
    consulta.prevision = fonasa.consultar_prevision(rut)
    if consulta.prevision['prevision'] != PrevisionService.FONASA:
        consulta.motivo_rechazo = MENSAJES_RECHAZO[consulta.prevision['prevision']]
    return consulta


@transaction.atomic
def registrar_paciente(consulta):
    """Crea o actualiza a la persona con los datos oficiales. Solo si puede recibir codigo."""
    assert consulta.puede_recibir_codigo
    if consulta.es_tutor:
        return consulta.usuario
    datos = consulta.inscripcion
    usuario = consulta.usuario or Usuario(username=f'rut_{consulta.rut}', rut=consulta.rut,
                                          tipo_usuario=Usuario.Tipo.PACIENTE)
    if usuario._state.adding:  # usuario nuevo (el UUID existe antes de guardar, por eso no se usa pk)
        usuario.set_unusable_password()  # entra solo con su huella, nunca con clave
    usuario.first_name, usuario.last_name = datos['nombres'], datos['apellidos']
    if datos.get('telefono'):
        usuario.telefono = datos['telefono']
    usuario.save()
    sector = None
    if datos.get('sector'):
        sector, _ = Sector.objects.get_or_create(nombre=datos['sector'], defaults={'comuna': 'La Granja'})
    paciente, creado = Paciente.objects.get_or_create(usuario=usuario)
    paciente.sector = sector
    paciente.prevision = Paciente.Prevision.FONASA
    paciente.tramo = consulta.prevision.get('tramo', '')
    paciente.estado_inscripcion = Paciente.Estado.VIGENTE
    paciente.prevision_consultada_en = timezone.now()
    if creado or not paciente.ficha_clinica_id:
        paciente.ficha_clinica_id = f'FC-{Paciente.objects.count() + 1000}'
    paciente.save()
    consulta.usuario = usuario
    return usuario
