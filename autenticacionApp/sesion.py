"""
Quien esta usando el sistema y por quien actua (RN-07: cada rol ve solo lo suyo).

- Paciente: actua por si mismo.
- Tutor: elige a una de las personas que tiene a cargo (RF-03).
- SOME: administrativo o personal del CESFAM (is_staff).
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import Paciente, Usuario

CLAVE_PACIENTE = 'paciente_activo_id'


def es_some(usuario):
    return usuario.is_authenticated and (usuario.is_staff or usuario.tipo_usuario == Usuario.Tipo.ADMINISTRATIVO)


def pacientes_a_cargo(usuario):
    return Paciente.objects.filter(tutor=usuario).select_related('usuario', 'sector')


def paciente_activo(request):
    """Paciente por el que se esta actuando, o None."""
    usuario = request.user
    if not usuario.is_authenticated:
        return None
    if usuario.tipo_usuario == Usuario.Tipo.PACIENTE:
        return Paciente.objects.filter(usuario=usuario).select_related('usuario', 'sector').first()
    if usuario.tipo_usuario == Usuario.Tipo.TUTOR:
        # El id guardado en la sesion se vuelve a validar: el tutor solo puede actuar por sus dependientes
        return pacientes_a_cargo(usuario).filter(pk=request.session.get(CLAVE_PACIENTE)).first()
    return None


def requiere_paciente(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('ingresar')
        from .privacidad import consentimiento_vigente  # evita importacion circular
        if request.user.tipo_usuario in (Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR) and                 not consentimiento_vigente(request.user):
            return redirect('aceptar_politica')  # B-07: politica nueva o retirada
        paciente = paciente_activo(request)
        if paciente is None:
            if request.user.tipo_usuario == Usuario.Tipo.TUTOR:
                return redirect('elegir_paciente')
            messages.warning(request, 'Esta sección es para pacientes y tutores.')
            return redirect('inicio')
        request.paciente = paciente
        return vista(request, *args, **kwargs)
    return envoltura


def es_admin_cesfam(usuario):
    return usuario.is_authenticated and usuario.tipo_usuario == Usuario.Tipo.ADMINISTRADOR


def es_profesional(usuario):
    return usuario.is_authenticated and usuario.tipo_usuario == Usuario.Tipo.PROFESIONAL


def _exigir(condicion, aviso, ingreso='ingresar'):
    """Decorador: sesión iniciada + condición + (B-20) clave temporal ya cambiada."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(ingreso)
            if not condicion(request.user):
                messages.warning(request, aviso)
                return redirect('inicio')
            if request.user.debe_cambiar_clave:
                return redirect('personal_cambiar_clave')
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


requiere_some = _exigir(es_some, 'Esta sección es solo para el personal del SOME.')
requiere_administrador = _exigir(es_admin_cesfam, 'Esta sección es solo para el Administrador CESFAM.',
                                 'personal_ingresar')
requiere_profesional = _exigir(es_profesional, 'Esta sección es solo para profesionales.', 'personal_ingresar')


def contexto_sesion(request):
    """Context processor: deja estos datos disponibles en todas las plantillas."""
    usuario = getattr(request, 'user', None)
    if not usuario or not usuario.is_authenticated:
        return {}
    return {
        'paciente_activo': paciente_activo(request),
        'es_tutor': usuario.tipo_usuario == Usuario.Tipo.TUTOR,
        'es_some': es_some(usuario),
        'es_admin_cesfam': es_admin_cesfam(usuario),
        'es_profesional': es_profesional(usuario),
    }
