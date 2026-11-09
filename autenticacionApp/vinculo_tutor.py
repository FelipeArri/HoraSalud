"""
B-10 · Vínculo de tutor o cuidador (RF-03).

Un tutor pide y cancela horas por otra persona. El vínculo lo autoriza:
- el propio paciente, desde "Mis datos", o
- el SOME, en persona (menores o personas que no usan la app), con la
  autorización del paciente o de su representante legal.

El paciente (o el SOME) puede quitar el vínculo cuando quiera. Si el tutor aún no
existe, se crea su cuenta sin huella: la activa en el SOME, que revisa su cédula
en persona (enrolamiento con código, B-06). Autorizar y revocar queda en el
registro de auditoría (RN-11).

Limitación del prototipo: una persona tiene un solo tipo de usuario, así que un
paciente no puede ser tutor de otro paciente a la vez.
"""
from django.db import transaction

from .models import RegistroAuditoria, Usuario
from .personal import auditar


class VinculoError(Exception):
    """Regla de negocio del vínculo que no se cumple (mensaje listo para mostrar)."""


def _buscar_o_crear_tutor(rut, nombres, apellidos):
    existente = Usuario.objects.filter(rut=rut).first()
    if existente is None:
        if not nombres.strip() or not apellidos.strip():
            raise VinculoError('Escribe los nombres y apellidos de tu tutor.')
        tutor = Usuario(username=f'rut_{rut}', rut=rut, tipo_usuario=Usuario.Tipo.TUTOR,
                        first_name=nombres.strip()[:150], last_name=apellidos.strip()[:150])
        tutor.set_unusable_password()  # entra solo con su huella, nunca con clave
        tutor.save()
        return tutor, True
    if existente.tipo_usuario != Usuario.Tipo.TUTOR:
        # Paciente o funcionario: no se cambia su tipo de cuenta desde aquí
        raise VinculoError('Ese RUT ya tiene otro tipo de cuenta en HoraSalud y no puede ser tutor. '
                           'Acércate al SOME para revisarlo.')
    if not existente.is_active:
        raise VinculoError('La cuenta de ese tutor está desactivada. Acércate al SOME.')
    return existente, False


@transaction.atomic
def autorizar(paciente, rut, nombres='', apellidos='', request=None, por_some=False):
    """Deja a la persona con ese RUT como tutor del paciente. Devuelve (tutor, cuenta_nueva)."""
    if paciente.tutor_id:
        raise VinculoError('Ya tienes un tutor. Quítalo primero si quieres cambiarlo.')
    if rut == paciente.usuario.rut:
        raise VinculoError('No puedes ser tu propio tutor.')
    tutor, nuevo = _buscar_o_crear_tutor(rut, nombres, apellidos)
    paciente.tutor = tutor
    paciente.save(update_fields=['tutor'])
    quien = 'SOME en persona' if por_some else 'el paciente desde la app'
    auditar(request, RegistroAuditoria.Accion.TUTOR_AUTORIZADO, objetivo=paciente.usuario,
            detalle=f'Tutor {tutor.rut} autorizado por {quien}{" (cuenta nueva)" if nuevo else ""}')
    return tutor, nuevo


@transaction.atomic
def revocar(paciente, request=None, por_some=False):
    """Quita el tutor. Desde ese momento ya no puede actuar por el paciente."""
    tutor = paciente.tutor
    if tutor is None:
        raise VinculoError('No tienes un tutor autorizado.')
    paciente.tutor = None
    paciente.save(update_fields=['tutor'])
    quien = 'SOME en persona' if por_some else 'el paciente desde la app'
    auditar(request, RegistroAuditoria.Accion.TUTOR_REVOCADO, objetivo=paciente.usuario,
            detalle=f'Tutor {tutor.rut} revocado por {quien}')
    return tutor
