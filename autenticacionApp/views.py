"""
Ingreso al sistema (RF-01, RF-03).

Paso 1: el usuario escribe su RUT. Paso 2: confirma su identidad.
En este prototipo el paso 2 es una SIMULACION de la huella (solo con
DJANGO_DEBUG=True). En el bloque B-06 se reemplaza por passkeys (WebAuthn).
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import IngresoRutForm
from .models import Usuario
from .sesion import CLAVE_PACIENTE, es_some, pacientes_a_cargo

CLAVE_RUT_PENDIENTE = 'rut_pendiente'
TIPOS_CON_INGRESO = [Usuario.Tipo.PACIENTE, Usuario.Tipo.TUTOR, Usuario.Tipo.ADMINISTRATIVO]


def _destino(usuario):
    if es_some(usuario):
        return 'some_nomina'
    if usuario.tipo_usuario == Usuario.Tipo.TUTOR:
        return 'elegir_paciente'
    return 'mi_inicio'


def ingresar(request):
    if request.user.is_authenticated:
        return redirect(_destino(request.user))
    form = IngresoRutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = Usuario.objects.filter(rut=form.cleaned_data['rut'], is_active=True,
                                         tipo_usuario__in=TIPOS_CON_INGRESO).first()
        if usuario is None:
            # Mensaje generico: no revela si el RUT existe (OWASP A07)
            form.add_error('rut', 'No encontramos una inscripción activa con ese RUT. '
                                  'Acércate al SOME para inscribirte.')
        else:
            request.session[CLAVE_RUT_PENDIENTE] = usuario.rut
            return redirect('verificar')
    return render(request, 'autenticacionApp/ingresar.html', {'form': form})


def verificar(request):
    if not settings.HORASALUD_INGRESO_DEMO:
        raise Http404  # sin passkeys (B-06) no se permite entrar solo con RUT
    rut = request.session.get(CLAVE_RUT_PENDIENTE)
    usuario = Usuario.objects.filter(rut=rut, is_active=True, tipo_usuario__in=TIPOS_CON_INGRESO).first()
    if usuario is None:
        return redirect('ingresar')
    if request.method == 'POST':
        request.session.pop(CLAVE_RUT_PENDIENTE, None)
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')  # rota la sesion
        return redirect(_destino(usuario))
    return render(request, 'autenticacionApp/verificar.html', {'usuario': usuario})


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
    return redirect('inicio')
