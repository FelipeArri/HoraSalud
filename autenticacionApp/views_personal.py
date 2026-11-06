"""
B-20 · Pantallas del personal: ingreso con RUT + clave, cambio de clave,
gestión de funcionarios (Administrador CESFAM), auditoría y agenda del profesional.
"""
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import personal
from .forms import ConfirmarAdminForm, FuncionarioForm, IngresoPersonalForm
from .models import RegistroAuditoria, Usuario
from .sesion import requiere_administrador, requiere_profesional
from .views import _destino, _iniciar_sesion

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
            _iniciar_sesion(request, usuario)
            personal.auditar(request, RegistroAuditoria.Accion.INGRESO, actor=usuario, objetivo=usuario)
            if usuario.debe_cambiar_clave:
                return redirect('personal_cambiar_clave')
            return redirect(_destino(usuario))
    return render(request, 'autenticacionApp/personal_ingresar.html', {'form': form})


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
                  RegistroAuditoria.Accion.INGRESO_BLOQUEADO]  # DEF-07 y DEF-08


@requiere_administrador
def auditoria(request):
    ver = request.GET.get('ver', 'personal')
    registros = RegistroAuditoria.objects.select_related('actor', 'objetivo')
    if ver == 'horas':
        registros = registros.filter(accion__in=ACCIONES_HORAS)
    elif ver != 'todo':
        ver = 'personal'
        registros = registros.exclude(accion__in=ACCIONES_HORAS)
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
