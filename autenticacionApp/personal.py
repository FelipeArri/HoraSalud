"""
B-20 · Personal del CESFAM: ingreso con RUT + clave, administrador CESFAM y auditoría (RN-11).

- El personal (SOME, profesionales y Administrador CESFAM) entra con RUT + clave.
- 5 claves incorrectas seguidas bloquean la cuenta 15 minutos (OWASP A07).
- Para agregar, desactivar o dar clave temporal, el administrador vuelve a escribir
  SU clave. Si se equivoca 3 veces, se le cierra la sesión.
- Todo queda en RegistroAuditoria.
"""
import secrets
from datetime import timedelta

from django.contrib.auth import logout
from django.db import transaction
from django.utils import timezone

from .models import Profesional, RegistroAuditoria, Usuario

MAX_INTENTOS_INGRESO = 5
MINUTOS_BLOQUEO = 15
MAX_INTENTOS_REAUTENTICACION = 3
CLAVE_REAUTH = 'reautenticacion_fallida'
ALFABETO_CLAVE = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # sin 0/O, 1/l/I


class PersonalError(Exception):
    """Regla del personal no cumplida (mensaje apto para mostrar)."""


def _ip(request):
    return request.META.get('REMOTE_ADDR') if request else None


def auditar(request, accion, actor=None, objetivo=None, detalle=''):
    actor = actor or (request.user if request and request.user.is_authenticated else None)
    return RegistroAuditoria.objects.create(
        actor=actor, actor_rut=getattr(actor, 'rut', '') or '', accion=accion,
        objetivo=objetivo, objetivo_rut=getattr(objetivo, 'rut', '') or '',
        detalle=detalle[:200], ip=_ip(request))


def generar_clave(largo=12):
    """Clave temporal legible (sin caracteres que se confunden) con letras y números."""
    while True:
        clave = ''.join(secrets.choice(ALFABETO_CLAVE) for _ in range(largo))
        if any(c.isdigit() for c in clave) and any(c.isupper() for c in clave) and any(c.islower() for c in clave):
            return clave


# ---------- Ingreso ----------

def autenticar(request, rut, clave):
    """Devuelve el usuario si RUT + clave son correctos; si no, PersonalError con mensaje genérico."""
    generico = PersonalError('RUT o clave incorrectos.')
    usuario = Usuario.objects.filter(rut=rut, tipo_usuario__in=Usuario.PERSONAL).first()
    if usuario is None or not usuario.is_active:
        raise generico  # no revela si el RUT existe ni si está desactivado
    ahora = timezone.now()
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos = max(1, int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1)
        raise PersonalError(f'Cuenta bloqueada por intentos fallidos. Intenta en {minutos} minuto(s) '
                            'o pide al Administrador CESFAM una clave temporal.')
    if not usuario.check_password(clave):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= MAX_INTENTOS_INGRESO:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            usuario.intentos_fallidos = 0
            auditar(request, RegistroAuditoria.Accion.CUENTA_BLOQUEADA, actor=usuario, objetivo=usuario,
                    detalle=f'{MAX_INTENTOS_INGRESO} claves incorrectas: bloqueo de {MINUTOS_BLOQUEO} min')
        else:
            auditar(request, RegistroAuditoria.Accion.INGRESO_FALLIDO, actor=usuario, objetivo=usuario,
                    detalle=f'Intento {usuario.intentos_fallidos} de {MAX_INTENTOS_INGRESO}')
        usuario.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
        raise generico
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
    return usuario


def cambiar_clave(request, usuario, clave_nueva):
    usuario.set_password(clave_nueva)
    usuario.debe_cambiar_clave = False
    usuario.save(update_fields=['password', 'debe_cambiar_clave'])
    auditar(request, RegistroAuditoria.Accion.CAMBIO_CLAVE, actor=usuario, objetivo=usuario)


# ---------- Reautenticación del administrador ----------

def reautenticar(request, clave):
    """
    True si la clave del administrador es correcta. Si se equivoca 3 veces seguidas
    se cierra su sesión y devuelve None (la vista debe mandar a Ingresar).
    """
    usuario = request.user
    if clave and usuario.check_password(clave):
        request.session[CLAVE_REAUTH] = 0
        return True
    fallidos = request.session.get(CLAVE_REAUTH, 0) + 1
    auditar(request, RegistroAuditoria.Accion.REAUTENTICACION_FALLIDA,
            detalle=f'Intento {fallidos} de {MAX_INTENTOS_REAUTENTICACION}')
    if fallidos >= MAX_INTENTOS_REAUTENTICACION:
        auditar(request, RegistroAuditoria.Accion.SESION_CERRADA)
        logout(request)
        return None
    request.session[CLAVE_REAUTH] = fallidos
    return False


def intentos_restantes(request):
    return MAX_INTENTOS_REAUTENTICACION - request.session.get(CLAVE_REAUTH, 0)


# ---------- Gestión de funcionarios ----------

def funcionarios():
    return (Usuario.objects.filter(tipo_usuario__in=Usuario.PERSONAL)
            .select_related('profesional__especialidad').order_by('-is_active', 'tipo_usuario', 'last_name'))


@transaction.atomic
def crear_funcionario(request, *, rut, nombres, apellidos, tipo, especialidad=None, box='', email='', sector=None):
    """Crea la cuenta con una clave temporal que se entrega en persona. Devuelve (usuario, clave)."""
    if Usuario.objects.filter(rut=rut).exists():
        raise PersonalError('Ese RUT ya tiene una cuenta en HoraSalud.')
    clave = generar_clave()
    usuario = Usuario(username=f'func_{rut.replace("-", "")}', rut=rut, first_name=nombres, last_name=apellidos,
                      email=email, tipo_usuario=tipo, debe_cambiar_clave=True)
    usuario.set_password(clave)
    usuario.save()
    if tipo == Usuario.Tipo.PROFESIONAL:
        Profesional.objects.create(usuario=usuario, especialidad=especialidad, box_atencion=box, sector=sector)
    auditar(request, RegistroAuditoria.Accion.ALTA, objetivo=usuario,
            detalle=f'{usuario.get_tipo_usuario_display()}' + (f' · {especialidad}' if especialidad else ''))
    return usuario, clave


def _administradores_activos():
    return Usuario.objects.filter(tipo_usuario=Usuario.Tipo.ADMINISTRADOR, is_active=True)


def cambiar_estado(request, funcionario, activo, motivo=''):
    if funcionario.pk == request.user.pk:
        raise PersonalError('No puedes desactivar tu propia cuenta.')
    if (not activo and funcionario.tipo_usuario == Usuario.Tipo.ADMINISTRADOR
            and _administradores_activos().count() <= 1):
        raise PersonalError('Debe quedar al menos un Administrador CESFAM activo.')
    funcionario.is_active = activo
    funcionario.save(update_fields=['is_active'])
    accion = RegistroAuditoria.Accion.REACTIVACION if activo else RegistroAuditoria.Accion.DESACTIVACION
    auditar(request, accion, objetivo=funcionario, detalle=motivo)


def dar_clave_temporal(request, funcionario):
    if funcionario.pk == request.user.pk:
        raise PersonalError('Para tu propia cuenta usa "Cambiar mi clave".')
    clave = generar_clave()
    funcionario.set_password(clave)
    funcionario.debe_cambiar_clave = True
    funcionario.intentos_fallidos = 0
    funcionario.bloqueado_hasta = None  # también desbloquea
    funcionario.save(update_fields=['password', 'debe_cambiar_clave', 'intentos_fallidos', 'bloqueado_hasta'])
    auditar(request, RegistroAuditoria.Accion.CLAVE_TEMPORAL, objetivo=funcionario)
    return clave


def horas_futuras_del_profesional(funcionario):
    from agendaApp.models import Hora  # evita importación circular
    return Hora.objects.filter(bloque__agenda__profesional__usuario=funcionario,
                               bloque__agenda__fecha__gte=timezone.localdate(),
                               estado__in=[Hora.Estado.RESERVADA, Hora.Estado.CONFIRMADA]).count()
