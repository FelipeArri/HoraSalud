"""
CC-19 · Segundo factor (MFA) para el personal del CESFAM (RNF-SEC02, OWASP A07, ISO 27001 8.5).

El personal ve datos de salud de muchas personas: una clave robada no debe bastar.

Ingreso:  RUT + clave (algo que sabe)  ->  passkey del PC o del teléfono (algo que tiene,
          desbloqueado con huella, rostro o PIN)  ->  recién ahí se abre la sesión.

Activación (primera vez o dispositivo perdido): solo se puede registrar una passkey justo
después de entrar con una clave entregada EN PERSONA por el Administrador CESFAM
(clave temporal o cuenta recién creada que nunca ha entrado). Así, quien robe una clave
de uso diario no puede registrar su propio dispositivo.

Entre el paso 1 y el 2 el usuario NO tiene sesión: solo queda anotado en la sesión anónima
quién pasó la clave, por 5 minutos.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Usuario

CLAVE_PENDIENTE = 'mfa_personal_id'
CLAVE_HASTA = 'mfa_personal_hasta'
VIGENCIA = timedelta(minutes=5)


def activo():
    """Se puede apagar solo por configuración (por ejemplo en pruebas del primer factor)."""
    return getattr(settings, 'HORASALUD_MFA_PERSONAL', True)


def iniciar(request, usuario):
    """La clave fue correcta: falta el segundo factor."""
    request.session.cycle_key()  # nueva sesión anónima (evita fijación de sesión)
    request.session[CLAVE_PENDIENTE] = str(usuario.pk)
    request.session[CLAVE_HASTA] = (timezone.now() + VIGENCIA).timestamp()


def pendiente(request):
    """Funcionario que ya escribió bien su clave y aún no confirma el segundo factor, o None."""
    hasta = request.session.get(CLAVE_HASTA)
    if not hasta or timezone.now().timestamp() > hasta:
        limpiar(request)
        return None
    return Usuario.objects.filter(pk=request.session.get(CLAVE_PENDIENTE), is_active=True,
                                  tipo_usuario__in=Usuario.PERSONAL).first()


def limpiar(request):
    request.session.pop(CLAVE_PENDIENTE, None)
    request.session.pop(CLAVE_HASTA, None)


def puede_registrar(usuario):
    """Registrar un dispositivo solo con una clave entregada en persona por el Administrador."""
    return usuario.debe_cambiar_clave or usuario.last_login is None
