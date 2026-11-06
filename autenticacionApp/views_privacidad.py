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
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import inscripcion, privacidad, vinculo_tutor
from .forms import IngresoRutForm, TutorForm
from .models import CodigoEnrolamiento, SolicitudDerechos, Usuario
from .sesion import pacientes_a_cargo, requiere_some

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


def _mis_datos(request, tutor_form=None):
    usuario = request.user
    paciente = getattr(usuario, 'paciente', None)
    if paciente and not paciente.tutor_id and tutor_form is None:
        tutor_form = TutorForm()
    return render(request, 'autenticacionApp/mis_datos.html', {
        **_contexto_politica(),
        'paciente': paciente,
        'tutor_form': tutor_form,
        'a_cargo': pacientes_a_cargo(usuario) if usuario.tipo_usuario == Usuario.Tipo.TUTOR else None,
        'consentimiento': usuario.consentimientos.filter(aceptado=True).first(),
        'dispositivos': usuario.passkeys.order_by('-creada_en'),
        'solicitudes': usuario.solicitudes_derechos.order_by('-creada_en')[:10],
        'tipos_solicitud': SolicitudDerechos.Tipo.choices,
    })


@requiere_persona
def mis_datos(request):
    return _mis_datos(request)


# ---------- B-10 · Mi tutor (RF-03) ----------

def _paciente_propio(request):
    """Solo el paciente maneja su tutor (el tutor no puede autorizarse ni quitarse a sí mismo aquí)."""
    if request.user.tipo_usuario != Usuario.Tipo.PACIENTE:
        return None
    return getattr(request.user, 'paciente', None)


@require_POST
@requiere_persona
def autorizar_tutor(request):
    paciente = _paciente_propio(request)
    if paciente is None:
        messages.warning(request, 'Solo el paciente puede autorizar a su tutor.')
        return redirect('mis_datos')
    if paciente.tutor_id:  # la pantalla ya no muestra el formulario: se avisa arriba
        messages.error(request, 'Ya tienes un tutor. Quítalo primero si quieres cambiarlo.')
        return redirect('mis_datos')
    form = TutorForm(request.POST)
    if not form.is_valid():
        return _mis_datos(request, tutor_form=form)
    try:
        tutor, nuevo = vinculo_tutor.autorizar(paciente, form.cleaned_data['rut'], form.cleaned_data['nombres'],
                                               form.cleaned_data['apellidos'], request=request)
    except vinculo_tutor.VinculoError as error:
        form.add_error(None, str(error))
        return _mis_datos(request, tutor_form=form)
    if nuevo or not tutor.passkeys.exists():
        messages.success(request, f'Autorizaste a {tutor.get_full_name()}. Para entrar, debe activar su huella '
                                  'en el SOME del CESFAM con su cédula de identidad.')
    else:
        messages.success(request, f'Autorizaste a {tutor.get_full_name()}. Ya puede pedir horas por ti.')
    return redirect('mis_datos')


@require_POST
@requiere_persona
def quitar_tutor(request):
    paciente = _paciente_propio(request)
    if paciente is None:
        messages.warning(request, 'Solo el paciente puede quitar a su tutor.')
        return redirect('mis_datos')
    try:
        tutor = vinculo_tutor.revocar(paciente, request=request)
    except vinculo_tutor.VinculoError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f'{tutor.get_full_name()} ya no puede pedir ni cancelar horas por ti.')
    return redirect('mis_datos')


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


# ---------- SOME: vínculos de tutor (B-10 · RF-03) ----------

TEXTO_AUTORIZACION_SOME = ('El paciente, o su representante legal, está presente y autoriza a esta persona '
                           'a pedir y cancelar horas por él.')


def _consultar_paciente_some(rut):
    """Devuelve (consulta, motivo_rechazo). Siempre vuelve a consultar el sistema clínico y FONASA (B-18)."""
    otro = Usuario.objects.filter(rut=rut).exclude(tipo_usuario=Usuario.Tipo.PACIENTE).first()
    if otro:
        return None, 'Ese RUT es de un tutor o de un funcionario, no de un paciente.'
    consulta = inscripcion.consultar(rut)
    if not consulta.puede_recibir_codigo:
        return consulta, consulta.motivo_rechazo
    return consulta, ''


@requiere_some
def some_tutores(request):
    """El SOME autoriza o quita el tutor de un paciente que está en ventanilla."""
    rut_form = IngresoRutForm(request.POST or request.GET or None)
    tutor_form = TutorForm(request.POST if request.POST.get('accion') == 'autorizar' else None, prefix='tutor')
    tutor_form.fields['confirmo'].label = TEXTO_AUTORIZACION_SOME
    tutor_form.fields['confirmo'].error_messages['required'] = 'Confirma que el paciente o su representante lo autoriza.'
    consulta, rechazo, paciente = None, '', None

    if rut_form.is_bound and rut_form.is_valid():
        consulta, rechazo = _consultar_paciente_some(rut_form.cleaned_data['rut'])
        if consulta and consulta.usuario:
            paciente = getattr(consulta.usuario, 'paciente', None)

        accion = request.POST.get('accion')
        if request.method == 'POST' and not rechazo:
            try:
                if accion == 'autorizar' and tutor_form.is_valid():
                    paciente = inscripcion.registrar_paciente(consulta).paciente  # menor sin cuenta: se crea aquí
                    tutor, nuevo = vinculo_tutor.autorizar(
                        paciente, tutor_form.cleaned_data['rut'], tutor_form.cleaned_data['nombres'],
                        tutor_form.cleaned_data['apellidos'], request=request, por_some=True)
                    aviso = ' Para entrar debe activar su huella aquí mismo, en "Activar huella".' \
                        if nuevo or not tutor.passkeys.exists() else ''
                    messages.success(request, f'{tutor.get_full_name()} quedó como tutor de '
                                              f'{paciente.usuario.get_full_name()}.{aviso}')
                    return redirect(f"{reverse('some_tutores')}?rut={paciente.usuario.rut}")
                if accion == 'quitar' and paciente:
                    tutor = vinculo_tutor.revocar(paciente, request=request, por_some=True)
                    messages.success(request, f'{tutor.get_full_name()} ya no es tutor de '
                                              f'{paciente.usuario.get_full_name()}.')
                    return redirect(f"{reverse('some_tutores')}?rut={paciente.usuario.rut}")
            except vinculo_tutor.VinculoError as error:
                tutor_form.add_error(None, str(error))
            if paciente:
                paciente.refresh_from_db()

    return render(request, 'autenticacionApp/some_tutores.html', {
        'rut_form': rut_form, 'tutor_form': tutor_form, 'consulta': consulta, 'rechazo': rechazo,
        'paciente': paciente})


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
