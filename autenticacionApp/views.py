"""
Ingreso al sistema (RF-01, RF-03) y enrolamiento con passkeys (B-06).

Ingreso:      RUT -> huella / rostro / PIN del dispositivo (passkey) -> sesion.
Enrolamiento: el SOME valida la cedula en persona y entrega un codigo de un solo
              uso -> el paciente escribe RUT + codigo -> registra su passkey.

Modo demostracion (solo con DJANGO_DEBUG=True): permite entrar sin passkey
para probar el resto del sistema con los usuarios ficticios.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import passkeys
from .forms import EnrolamientoForm, IngresoRutForm
from .models import CodigoEnrolamiento, Usuario
from .sesion import CLAVE_PACIENTE, es_some, pacientes_a_cargo, requiere_some

CLAVE_RUT_PENDIENTE = 'rut_pendiente'
CLAVE_ENROLANDO = 'enrolamiento_codigo_id'
TIPOS_CON_INGRESO = [Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR, Usuario.Tipo.ADMINISTRATIVO]


def _destino(usuario):
    if es_some(usuario):
        return 'some_nomina'
    if usuario.tipo_usuario == Usuario.Tipo.TUTOR:
        return 'elegir_paciente'
    return 'mi_inicio'


def _iniciar_sesion(request, usuario):
    request.session.pop(CLAVE_RUT_PENDIENTE, None)
    request.session.pop(CLAVE_ENROLANDO, None)
    login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')  # rota la sesion


def _error_json(texto, estado=400):
    return JsonResponse({'ok': False, 'error': texto}, status=estado)


# ---------- Ingreso ----------

def ingresar(request):
    if request.user.is_authenticated:
        return redirect(_destino(request.user))
    form = IngresoRutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = passkeys.usuario_por_rut(form.cleaned_data['rut'], TIPOS_CON_INGRESO)
        if usuario is None:
            # Mensaje generico: no revela si el RUT existe (OWASP A07)
            form.add_error('rut', 'No encontramos una inscripción activa con ese RUT. '
                                  'Acércate al SOME para inscribirte.')
        else:
            request.session[CLAVE_RUT_PENDIENTE] = usuario.rut
            return redirect('verificar')
    return render(request, 'autenticacionApp/ingresar.html', {'form': form})


def _usuario_pendiente(request):
    return passkeys.usuario_por_rut(request.session.get(CLAVE_RUT_PENDIENTE), TIPOS_CON_INGRESO)


def verificar(request):
    usuario = _usuario_pendiente(request)
    if usuario is None:
        return redirect('ingresar')
    if request.method == 'POST':
        # Boton "entrar sin huella": SOLO en modo demostracion
        if not passkeys.modo_demo_permitido(request):
            raise Http404
        _iniciar_sesion(request, usuario)
        return redirect(_destino(usuario))
    return render(request, 'autenticacionApp/verificar.html', {
        'usuario': usuario,
        'tiene_passkey': passkeys.passkeys_del_dominio(request, usuario).exists(),
        'modo_demo': passkeys.modo_demo_permitido(request),
        'rp_id': passkeys.rp_id_para(request),
    })


@require_POST
def passkey_ingreso_opciones(request):
    usuario = _usuario_pendiente(request)
    if usuario is None or not passkeys.passkeys_del_dominio(request, usuario).exists():
        return _error_json('Primero escribe tu RUT.', 403)
    return JsonResponse({'ok': True, 'opciones': passkeys.opciones_ingreso(request, usuario)})


@require_POST
def passkey_ingreso_verificar(request):
    usuario = _usuario_pendiente(request)
    if usuario is None:
        return _error_json('Primero escribe tu RUT.', 403)
    try:
        passkeys.verificar_ingreso(request, usuario, request.body.decode())
    except passkeys.PasskeyError as error:
        return _error_json(str(error))
    _iniciar_sesion(request, usuario)
    return JsonResponse({'ok': True, 'destino': reverse(_destino(usuario))})


# ---------- Enrolamiento del paciente ----------

def enrolar(request):
    """Paso 1: RUT + codigo de un solo uso entregado por el SOME."""
    form = EnrolamientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = passkeys.usuario_por_rut(form.cleaned_data['rut'], TIPOS_CON_INGRESO)
        try:
            if usuario is None:
                raise passkeys.PasskeyError('El código no es válido o ya venció. Pide uno nuevo en el SOME.')
            codigo = passkeys.validar_codigo(usuario, form.cleaned_data['codigo'])
        except passkeys.PasskeyError as error:
            form.add_error('codigo', str(error))
        else:
            request.session[CLAVE_ENROLANDO] = codigo.pk
            return redirect('enrolar_huella')
    return render(request, 'autenticacionApp/enrolar.html', {'form': form})


def _codigo_en_curso(request):
    return (CodigoEnrolamiento.objects.select_related('usuario')
            .filter(pk=request.session.get(CLAVE_ENROLANDO), usado_en__isnull=True,
                    expira_en__gt=timezone.now()).first())


def enrolar_huella(request):
    """Paso 2: el dispositivo crea la passkey (pide huella, rostro o PIN)."""
    codigo = _codigo_en_curso(request)
    if codigo is None:
        messages.warning(request, 'Escribe tu RUT y el código que te entregó el SOME.')
        return redirect('enrolar')
    return render(request, 'autenticacionApp/enrolar_huella.html', {
        'usuario': codigo.usuario, 'rp_id': passkeys.rp_id_para(request)})


@require_POST
def passkey_registro_opciones(request):
    codigo = _codigo_en_curso(request)
    if codigo is None:
        return _error_json('El código venció. Pide uno nuevo en el SOME.', 403)
    return JsonResponse({'ok': True, 'opciones': passkeys.opciones_registro(request, codigo.usuario)})


@require_POST
def passkey_registro_verificar(request):
    codigo = _codigo_en_curso(request)
    if codigo is None:
        return _error_json('El código venció. Pide uno nuevo en el SOME.', 403)
    dispositivo = request.headers.get('X-Dispositivo', '')
    try:
        passkeys.verificar_registro(request, codigo.usuario, request.body.decode(), dispositivo)
    except passkeys.PasskeyError as error:
        return _error_json(str(error))
    codigo.usado_en = timezone.now()  # el codigo ya no sirve otra vez
    codigo.save(update_fields=['usado_en'])
    _iniciar_sesion(request, codigo.usuario)
    messages.success(request, '¡Listo! Desde ahora entras con tu huella, tu rostro o el PIN de tu dispositivo.')
    return JsonResponse({'ok': True, 'destino': reverse(_destino(codigo.usuario))})


# ---------- SOME: generar el codigo ----------

@requiere_some
def some_enrolar(request):
    """El funcionario busca al paciente por RUT, valida su cedula EN PERSONA y genera el codigo."""
    form = IngresoRutForm(request.POST or request.GET or None)
    usuario, codigo = None, None
    if form.is_bound and form.is_valid():
        usuario = passkeys.usuario_por_rut(form.cleaned_data['rut'], [Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR])
        if usuario is None:
            form.add_error('rut', 'No hay un paciente o tutor inscrito con ese RUT.')
        elif request.method == 'POST' and request.POST.get('cedula_validada') == 'si':
            codigo = passkeys.generar_codigo(usuario, request.user)
        elif request.method == 'POST':
            messages.error(request, 'Confirma que revisaste la cédula de identidad en persona.')
    return render(request, 'autenticacionApp/some_enrolar.html', {
        'form': form, 'usuario': usuario, 'codigo': codigo,
        'url_activar': passkeys.url_publica(request, reverse('enrolar')),
        'vigencia_min': int(passkeys.VIGENCIA_CODIGO.total_seconds() // 60)})


# ---------- Tutor y salida ----------

def elegir_paciente(request):
    """RF-03: el tutor elige a quien le pedira la hora."""
    if not request.user.is_authenticated or request.user.tipo_usuario != Usuario.Tipo.TUTOR:
        return redirect('ingresar')
    a_cargo = pacientes_a_cargo(request.user)
    if request.method == 'POST':
        elegido = a_cargo.filter(pk=request.POST.get('paciente')).first()
        if elegido:
            request.session[CLAVE_PACIENTE] = str(elegido.pk)
            return redirect('mi_inicio')
        messages.error(request, 'Elige a una de las personas que tienes a cargo.')
    return render(request, 'autenticacionApp/elegir_paciente.html', {'a_cargo': a_cargo})


@require_POST
def salir(request):
    logout(request)  # borra la sesion completa
    messages.info(request, 'Cerraste tu sesión de forma segura.')
    respuesta = redirect('inicio')
    respuesta['Clear-Site-Data'] = '"cache"'  # DEF-03: borra las copias de paginas privadas
    return respuesta
