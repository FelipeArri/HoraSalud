"""
B-20 · Pantallas del personal: ingreso con RUT + clave, cambio de clave,
gestión de funcionarios (Administrador CESFAM), auditoría y agenda del profesional.
CC-19 · Segundo factor (MFA): después de la clave se pide la passkey del dispositivo.
"""
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import limite_intentos, passkeys, personal, segundo_factor
from .forms import ConfirmarAdminForm, FuncionarioForm, IngresoPersonalForm
from .models import RegistroAuditoria, Usuario
from .sesion import requiere_administrador, requiere_profesional
from .views import METODO_CLAVE, _destino, _error_json, _iniciar_sesion

METODO_MFA = 'Entró con RUT, clave y passkey del dispositivo (dos factores, MFA)'
METODO_MFA_ALTA = 'Entró con la clave entregada por el Administrador y registró su passkey (MFA)'
METODO_MFA_DEMO = 'Entró con RUT y clave SIN segundo factor (modo demostración, solo en el equipo local)'

AVISO_SESION_CERRADA = ('Se cerró tu sesión: escribiste mal tu clave de administrador 3 veces. '
                        'Quedó registrado en la auditoría.')


def ingresar(request):
    if request.user.is_authenticated and request.user.es_personal:
        return redirect(_destino(request.user))
    form = IngresoPersonalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            usuario = personal.autenticar(request, form.cleaned_data['rut'], form.cleaned_data['clave'])
        except personal.PersonalError as error:
            form.add_error(None, str(error))
        else:
            if segundo_factor.activo():
                segundo_factor.iniciar(request, usuario)  # CC-19: aún sin sesión
                return redirect('personal_segundo_factor')
            _iniciar_sesion(request, usuario, METODO_CLAVE)
            return redirect(_siguiente(usuario))
    return render(request, 'autenticacionApp/personal_ingresar.html', {'form': form})


def _siguiente(usuario):
    return 'personal_cambiar_clave' if usuario.debe_cambiar_clave else _destino(usuario)


# ---------- CC-19 · Segundo factor (MFA) ----------

def _completar_ingreso(request, usuario, metodo):
    segundo_factor.limpiar(request)
    limite_intentos.ingreso_correcto(usuario)
    _iniciar_sesion(request, usuario, metodo)
    return reverse(_siguiente(usuario))


def segundo_factor_vista(request):
    usuario = segundo_factor.pendiente(request)
    if usuario is None:
        messages.warning(request, 'Pasaron más de 5 minutos. Vuelve a escribir tu RUT y tu clave.')
        return redirect('personal_ingresar')
    if request.method == 'POST':
        # "Entrar sin segundo factor": SOLO en modo demostración en el equipo local
        if not passkeys.modo_demo_permitido(request):
            raise Http404
        return redirect(_completar_ingreso(request, usuario, METODO_MFA_DEMO))
    return render(request, 'autenticacionApp/personal_segundo_factor.html', {
        'usuario': usuario,
        'tiene_passkey': passkeys.passkeys_del_dominio(request, usuario).exists(),
        'puede_registrar': segundo_factor.puede_registrar(usuario),
        'modo_demo': passkeys.modo_demo_permitido(request),
        'rp_id': passkeys.rp_id_para(request),
    })


def _pendiente_json(request):
    usuario = segundo_factor.pendiente(request)
    if usuario is None:
        return None, _error_json('Pasaron más de 5 minutos. Vuelve a escribir tu RUT y tu clave.', 403)
    if limite_intentos.rut_bloqueado(usuario):
        return None, _error_json(limite_intentos.AVISO_RUT, 429)  # mismo límite que los pacientes
    return usuario, None


AVISO_SIN_PERMISO_REGISTRO = 'Para registrar un dispositivo pide al Administrador CESFAM una clave temporal.'


@require_POST
def mfa_ingreso_opciones(request):
    usuario, error = _pendiente_json(request)
    if error:
        return error
    if not passkeys.passkeys_del_dominio(request, usuario).exists():
        return _error_json('Aún no registras un dispositivo.', 403)
    return JsonResponse({'ok': True, 'opciones': passkeys.opciones_ingreso(request, usuario)})


@require_POST
def mfa_ingreso_verificar(request):
    usuario, error = _pendiente_json(request)
    if error:
        return error
    try:
        passkeys.verificar_ingreso(request, usuario, request.body.decode())
    except passkeys.PasskeyError as falla:
        if limite_intentos.registrar_huella_rechazada(request, usuario):
            segundo_factor.limpiar(request)
            return _error_json(limite_intentos.AVISO_RUT, 429)
        return _error_json(str(falla))
    return JsonResponse({'ok': True, 'destino': _completar_ingreso(request, usuario, METODO_MFA)})


@require_POST
def mfa_registro_opciones(request):
    usuario, error = _pendiente_json(request)
    if error:
        return error
    if not segundo_factor.puede_registrar(usuario):
        return _error_json(AVISO_SIN_PERMISO_REGISTRO, 403)
    return JsonResponse({'ok': True, 'opciones': passkeys.opciones_registro(request, usuario)})


@require_POST
def mfa_registro_verificar(request):
    usuario, error = _pendiente_json(request)
    if error:
        return error
    if not segundo_factor.puede_registrar(usuario):
        return _error_json(AVISO_SIN_PERMISO_REGISTRO, 403)
    try:
        passkeys.verificar_registro(request, usuario, request.body.decode(),
                                    request.headers.get('X-Dispositivo', ''))
    except passkeys.PasskeyError as falla:
        return _error_json(str(falla))
    messages.success(request, 'Dispositivo registrado. Desde ahora entras con tu clave y tu huella o PIN.')
    return JsonResponse({'ok': True, 'destino': _completar_ingreso(request, usuario, METODO_MFA_ALTA)})


def cambiar_clave(request):
    if not request.user.is_authenticated or not request.user.es_personal:
        return redirect('personal_ingresar')
    form = PasswordChangeForm(request.user, request.POST or None)
    for campo in form.fields.values():
        campo.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        personal.cambiar_clave(request, request.user, form.cleaned_data['new_password1'])
        _iniciar_sesion(request, request.user)  # la sesión sigue válida con la clave nueva
        messages.success(request, 'Tu clave quedó cambiada.')
        return redirect(_destino(request.user))
    return render(request, 'autenticacionApp/personal_cambiar_clave.html', {
        'form': form, 'obligatorio': request.user.debe_cambiar_clave})


# ---------- Administrador CESFAM ----------

@requiere_administrador
def funcionarios(request):
    lista = personal.funcionarios()
    return render(request, 'autenticacionApp/personal_funcionarios.html', {
        'activos': [f for f in lista if f.is_active],
        'inactivos': [f for f in lista if not f.is_active],
        'ahora': timezone.now(),
    })


@requiere_administrador
def funcionario_nuevo(request):
    form = FuncionarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        confirmado = personal.reautenticar(request, form.cleaned_data['clave_admin'])
        if confirmado is None:
            messages.error(request, AVISO_SESION_CERRADA)
            return redirect('personal_ingresar')
        if not confirmado:
            form.add_error('clave_admin', f'Clave incorrecta. Te quedan {personal.intentos_restantes(request)} '
                                          'intento(s) antes de cerrar la sesión.')
        else:
            datos = form.cleaned_data
            try:
                nuevo, clave = personal.crear_funcionario(
                    request, rut=datos['rut'], nombres=datos['nombres'], apellidos=datos['apellidos'],
                    tipo=datos['tipo'], especialidad=datos['especialidad'], box=datos['box'], email=datos['email'],
                    sector=datos['sector'])
            except personal.PersonalError as error:
                form.add_error('rut', str(error))
            else:
                # Se muestra UNA vez: no se guarda en ningún lado (solo su hash)
                return render(request, 'autenticacionApp/personal_clave_entregada.html',
                              {'funcionario': nuevo, 'clave': clave, 'nuevo': True})
    return render(request, 'autenticacionApp/personal_funcionario_nuevo.html', {
        'form': form, 'intentos': personal.intentos_restantes(request)})


ACCIONES = {
    'desactivar': 'Desactivar cuenta',
    'reactivar': 'Reactivar cuenta',
    'clave': 'Entregar clave temporal',
    'dispositivos': 'Quitar dispositivos registrados (segundo factor)',
}


@requiere_administrador
def funcionario_accion(request, pk, accion):
    if accion not in ACCIONES:
        raise Http404
    funcionario = get_object_or_404(Usuario, pk=pk, tipo_usuario__in=Usuario.PERSONAL)
    form = ConfirmarAdminForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        confirmado = personal.reautenticar(request, form.cleaned_data['clave_admin'])
        if confirmado is None:
            messages.error(request, AVISO_SESION_CERRADA)
            return redirect('personal_ingresar')
        if not confirmado:
            form.add_error('clave_admin', f'Clave incorrecta. Te quedan {personal.intentos_restantes(request)} '
                                          'intento(s) antes de cerrar la sesión.')
        else:
            try:
                if accion == 'clave':
                    clave = personal.dar_clave_temporal(request, funcionario)
                    return render(request, 'autenticacionApp/personal_clave_entregada.html',
                                  {'funcionario': funcionario, 'clave': clave, 'nuevo': False})
                if accion == 'dispositivos':  # CC-19: teléfono o PC perdido
                    cantidad = personal.quitar_dispositivos(request, funcionario, form.cleaned_data['motivo'])
                    messages.success(request, f'{funcionario.get_full_name()}: se quitaron {cantidad} '
                                              'dispositivo(s). Entrégale una clave temporal para registrar uno nuevo.')
                    return redirect('personal_funcionarios')
                personal.cambiar_estado(request, funcionario, accion == 'reactivar', form.cleaned_data['motivo'])
            except personal.PersonalError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, f'{funcionario.get_full_name()}: cuenta '
                                          f'{"reactivada" if accion == "reactivar" else "desactivada"}.')
            return redirect('personal_funcionarios')
    return render(request, 'autenticacionApp/personal_confirmar.html', {
        'form': form, 'funcionario': funcionario, 'accion': accion, 'titulo': ACCIONES[accion],
        'intentos': personal.intentos_restantes(request),
        'horas_futuras': personal.horas_futuras_del_profesional(funcionario) if accion == 'desactivar' else 0,
    })


ACCIONES_HORAS = [RegistroAuditoria.Accion.RESERVA, RegistroAuditoria.Accion.CANCELACION,
                  RegistroAuditoria.Accion.NO_SHOW, RegistroAuditoria.Accion.ATENDIDA,
                  RegistroAuditoria.Accion.INGRESO_BLOQUEADO,  # DEF-07 y DEF-08
                  RegistroAuditoria.Accion.TUTOR_AUTORIZADO, RegistroAuditoria.Accion.TUTOR_REVOCADO,
                  RegistroAuditoria.Accion.TUTOR_ACTUA,  # B-10
                  RegistroAuditoria.Accion.ESPERA_ALTA, RegistroAuditoria.Accion.ESPERA_BAJA,
                  RegistroAuditoria.Accion.CUPO_ACEPTADO]  # B-14
ROLES_PERSONAS = [Usuario.Tipo.PACIENTE.label, Usuario.Tipo.TUTOR.label]


@requiere_administrador
def auditoria(request):
    ver = request.GET.get('ver', 'personal')
    registros = RegistroAuditoria.objects.select_related('actor', 'objetivo')
    # Pacientes y tutores: sus horas, sus ingresos y salidas, y el vínculo de tutor
    de_personas = Q(accion__in=ACCIONES_HORAS) | Q(actor_rol__in=ROLES_PERSONAS)
    if ver == 'horas':
        registros = registros.filter(de_personas)
    elif ver != 'todo':
        ver = 'personal'
        registros = registros.exclude(de_personas)
    return render(request, 'autenticacionApp/personal_auditoria.html', {'registros': registros[:100], 'ver': ver})


# ---------- Profesional ----------

@requiere_profesional
def profesional_agenda(request):
    from agendaApp.models import Hora  # evita importación circular
    hoy = timezone.localdate()
    horas = (Hora.objects.filter(bloque__agenda__profesional__usuario=request.user, bloque__agenda__fecha=hoy)
             .exclude(estado=Hora.Estado.CANCELADA)
             .select_related('paciente__usuario', 'bloque__agenda__especialidad'))
    return render(request, 'autenticacionApp/profesional_agenda.html', {'horas': horas, 'hoy': hoy})
