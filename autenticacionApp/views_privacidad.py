"""
B-07 · Consentimiento y derechos ARCO+ (Ley 21.719).

- Politica de privacidad publica, en lenguaje simple.
- Consentimiento al activar la huella (antes de crear la passkey) y al ingresar
  si la politica cambio de version.
- "Mis datos": ver, descargar (acceso y portabilidad), borrar dispositivos,
  retirar el consentimiento y pedir rectificacion, supresion, oposicion o bloqueo.
- El SOME resuelve las solicitudes, porque los datos oficiales estan en el sistema clinico.
"""
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import privacidad
from .models import CodigoEnrolamiento, SolicitudDerechos, Usuario
from .sesion import requiere_some

TIPOS_PERSONA = [Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR]
CLAVE_ENROLANDO = 'enrolamiento_codigo_id'  # la misma que usa views.enrolar


def _contexto_politica():
    return {'version_politica': privacidad.VERSION_POLITICA}


def politica(request):
    return render(request, 'autenticacionApp/politica.html', _contexto_politica())


# ---------- Consentimiento durante el enrolamiento ----------

def _codigo_en_curso(request):
    return (CodigoEnrolamiento.objects.select_related('usuario')
            .filter(pk=request.session.get(CLAVE_ENROLANDO), usado_en__isnull=True,
                    expira_en__gt=timezone.now()).first())


def enrolar_consentimiento(request):
    """Paso intermedio: antes de crear la passkey, la persona acepta (o no) la política."""
    codigo = _codigo_en_curso(request)
    if codigo is None:
        messages.warning(request, 'Escribe tu RUT y el código que te entregó el SOME.')
        return redirect('enrolar')
    if request.method == 'POST':
        acepta = request.POST.get('decision') == 'acepto'
        privacidad.registrar(codigo.usuario, acepta)
        if acepta:
            return redirect('enrolar_huella')
        request.session.pop(CLAVE_ENROLANDO, None)
        return render(request, 'autenticacionApp/sin_consentimiento.html')
    return render(request, 'autenticacionApp/consentimiento.html', {
        **_contexto_politica(), 'usuario': codigo.usuario, 'en_enrolamiento': True})


# ---------- Consentimiento al ingresar (nueva versión de la política) ----------

def aceptar_politica(request):
    if not request.user.is_authenticated or request.user.tipo_usuario not in TIPOS_PERSONA:
        return redirect('ingresar')
    if request.method == 'POST':
        acepta = request.POST.get('decision') == 'acepto'
        privacidad.registrar(request.user, acepta)
        if acepta:
            messages.success(request, 'Gracias. Registramos tu aceptación.')
            return redirect('mi_inicio' if request.user.tipo_usuario == Usuario.Tipo.PACIENTE else 'elegir_paciente')
        logout(request)
        return render(request, 'autenticacionApp/sin_consentimiento.html')
    return render(request, 'autenticacionApp/consentimiento.html', {
        **_contexto_politica(), 'usuario': request.user, 'en_enrolamiento': False})


# ---------- Mis datos (derechos ARCO+) ----------

def requiere_persona(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('ingresar')
        if request.user.tipo_usuario not in TIPOS_PERSONA:
            messages.warning(request, 'Esta sección es para pacientes y tutores.')
            return redirect('inicio')
        return vista(request, *args, **kwargs)
    return envoltura


@requiere_persona
def mis_datos(request):
    usuario = request.user
    return render(request, 'autenticacionApp/mis_datos.html', {
        **_contexto_politica(),
        'paciente': getattr(usuario, 'paciente', None),
        'consentimiento': usuario.consentimientos.filter(aceptado=True).first(),
        'dispositivos': usuario.passkeys.order_by('-creada_en'),
        'solicitudes': usuario.solicitudes_derechos.order_by('-creada_en')[:10],
        'tipos_solicitud': SolicitudDerechos.Tipo.choices,
    })


@requiere_persona
def descargar_mis_datos(request):
    """Derecho de acceso y portabilidad: archivo JSON con todo lo que HoraSalud guarda."""
    contenido = json.dumps(privacidad.exportar_datos(request.user), ensure_ascii=False, indent=2)
    respuesta = HttpResponse(contenido, content_type='application/json; charset=utf-8')
    respuesta['Content-Disposition'] = f'attachment; filename="mis-datos-horasalud-{request.user.rut}.json"'
    return respuesta


@require_POST
@requiere_persona
def borrar_dispositivo(request, passkey_id):
    dispositivo = get_object_or_404(request.user.passkeys, pk=passkey_id)  # solo los propios (OWASP A01)
    dispositivo.delete()
    restantes = request.user.passkeys.count()
    if restantes:
        messages.success(request, 'Eliminamos ese dispositivo. Ya no podrá ingresar con tu huella.')
    else:
        messages.warning(request, 'Eliminaste tu último dispositivo. Para volver a ingresar necesitarás un código nuevo del SOME.')
    return redirect('mis_datos')


@require_POST
@requiere_persona
def solicitar_derecho(request):
    tipo = request.POST.get('tipo')
    if tipo not in SolicitudDerechos.Tipo.values:
        messages.error(request, 'Elige qué quieres solicitar.')
        return redirect('mis_datos')
    SolicitudDerechos.objects.create(usuario=request.user, tipo=tipo,
                                     detalle=request.POST.get('detalle', '').strip()[:500])
    messages.success(request, 'Recibimos tu solicitud. El SOME la revisará y te responderá.')
    return redirect('mis_datos')


@require_POST
@requiere_persona
def retirar_consentimiento(request):
    """Retirar el consentimiento desactiva el ingreso con huella. Puede seguir atendiéndose en ventanilla."""
    usuario = request.user
    privacidad.retirar(usuario)
    usuario.passkeys.all().delete()
    logout(request)
    return render(request, 'autenticacionApp/sin_consentimiento.html', {'retirado': True})


# ---------- SOME: solicitudes de derechos ----------

@requiere_some
def some_solicitudes(request):
    if request.method == 'POST':
        solicitud = get_object_or_404(SolicitudDerechos, pk=request.POST.get('solicitud'),
                                      estado=SolicitudDerechos.Estado.PENDIENTE)
        solicitud.estado = SolicitudDerechos.Estado.RESUELTA
        solicitud.respuesta = request.POST.get('respuesta', '').strip()[:500]
        solicitud.resuelta_por = request.user
        solicitud.resuelta_en = timezone.now()
        solicitud.save()
        messages.success(request, 'Solicitud marcada como resuelta.')
        return redirect('some_solicitudes')
    return render(request, 'autenticacionApp/some_solicitudes.html', {
        'pendientes': SolicitudDerechos.objects.filter(estado=SolicitudDerechos.Estado.PENDIENTE)
                                               .select_related('usuario'),
        'resueltas': SolicitudDerechos.objects.filter(estado=SolicitudDerechos.Estado.RESUELTA)
                                              .select_related('usuario', 'resuelta_por').order_by('-resuelta_en')[:10],
    })
