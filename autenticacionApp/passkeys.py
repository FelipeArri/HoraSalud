"""
Passkeys (WebAuthn) y codigos de enrolamiento (B-06, RNF-SEC02, RF-01).

Como funciona:
1. El servidor manda un "reto" (numero aleatorio) al navegador.
2. El telefono o el PC pide la huella, el rostro o el PIN AL SISTEMA
   OPERATIVO y firma el reto con una clave privada que nunca sale del equipo.
3. El servidor verifica la firma con la clave publica guardada.

El servidor nunca recibe ni guarda datos biometricos (Ley 21.719).
"""
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from webauthn import (generate_authentication_options, generate_registration_options, options_to_json,
                      verify_authentication_response, verify_registration_response)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (AuthenticatorSelectionCriteria, PublicKeyCredentialDescriptor,
                                      ResidentKeyRequirement, UserVerificationRequirement)

from .models import CodigoEnrolamiento, CredencialPasskey, Usuario

CLAVE_RETO = 'webauthn_reto'
VIGENCIA_CODIGO = timedelta(minutes=30)


class PasskeyError(Exception):
    """Mensaje pensado para mostrarse al usuario."""


# ---------- Codigos de enrolamiento (los entrega el SOME en persona) ----------

def _hash_codigo(codigo):
    limpio = ''.join(c for c in str(codigo) if c.isdigit())
    return hmac.new(settings.SECRET_KEY.encode(), limpio.encode(), hashlib.sha256).hexdigest()


def generar_codigo(usuario, creado_por):
    """Devuelve el codigo en texto (se muestra una sola vez). En la base queda solo su hash."""
    codigo = f'{secrets.randbelow(10**8):08d}'
    with transaction.atomic():
        # Un codigo nuevo anula los anteriores que no se usaron
        CodigoEnrolamiento.objects.filter(usuario=usuario, usado_en__isnull=True).update(
            expira_en=timezone.now())
        CodigoEnrolamiento.objects.create(usuario=usuario, creado_por=creado_por,
                                          codigo_hash=_hash_codigo(codigo),
                                          expira_en=timezone.now() + VIGENCIA_CODIGO)
    return f'{codigo[:4]}-{codigo[4:]}'


def validar_codigo(usuario, codigo):
    """Devuelve el CodigoEnrolamiento vigente si coincide. Bloquea tras 5 intentos fallidos."""
    vigente = (CodigoEnrolamiento.objects
               .filter(usuario=usuario, usado_en__isnull=True, expira_en__gt=timezone.now(),
                       intentos__lt=CodigoEnrolamiento.MAX_INTENTOS)
               .first())
    error = PasskeyError('El código no es válido o ya venció. Pide uno nuevo en el SOME.')
    if vigente is None:
        raise error
    if not hmac.compare_digest(vigente.codigo_hash, _hash_codigo(codigo)):
        vigente.intentos += 1
        vigente.save(update_fields=['intentos'])
        raise error
    return vigente


# ---------- WebAuthn ----------

def _origenes():
    return settings.WEBAUTHN_ORIGENES


def _descriptor(credencial):
    return PublicKeyCredentialDescriptor(id=base64url_to_bytes(credencial.credencial_id))


def opciones_registro(request, usuario):
    opciones = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NOMBRE,
        user_id=usuario.id.bytes,
        user_name=usuario.rut or usuario.username,
        user_display_name=usuario.get_full_name() or usuario.username,
        exclude_credentials=[_descriptor(c) for c in usuario.passkeys.all()],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,  # exige huella, rostro o PIN
        ),
    )
    request.session[CLAVE_RETO] = bytes_to_base64url(opciones.challenge)
    return options_to_json(opciones)


def _reto(request):
    reto = request.session.pop(CLAVE_RETO, None)  # cada reto sirve una sola vez
    if not reto:
        raise PasskeyError('La solicitud venció. Vuelve a intentarlo.')
    return base64url_to_bytes(reto)


def verificar_registro(request, usuario, credencial_json, dispositivo=''):
    try:
        verificado = verify_registration_response(
            credential=credencial_json,
            expected_challenge=_reto(request),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=_origenes(),
            require_user_verification=True,
        )
    except PasskeyError:
        raise
    except Exception as error:  # firma, origen o reto invalidos
        raise PasskeyError('No pudimos registrar tu huella. Inténtalo otra vez.') from error
    return CredencialPasskey.objects.create(
        usuario=usuario,
        credencial_id=bytes_to_base64url(verificado.credential_id),
        clave_publica=verificado.credential_public_key,
        contador_firmas=verificado.sign_count,
        dispositivo=dispositivo[:120],
    )


def opciones_ingreso(request, usuario):
    opciones = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        allow_credentials=[_descriptor(c) for c in usuario.passkeys.all()],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    request.session[CLAVE_RETO] = bytes_to_base64url(opciones.challenge)
    return options_to_json(opciones)


def verificar_ingreso(request, usuario, credencial_json):
    try:
        credencial_id = json.loads(credencial_json)['id']
    except (ValueError, KeyError, TypeError):
        raise PasskeyError('Respuesta inválida del dispositivo.')
    # Solo se aceptan passkeys de ESTE usuario (OWASP A01)
    credencial = usuario.passkeys.filter(credencial_id=credencial_id).first()
    if credencial is None:
        raise PasskeyError('Esta huella no está registrada para tu RUT.')
    try:
        verificado = verify_authentication_response(
            credential=credencial_json,
            expected_challenge=_reto(request),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=_origenes(),
            credential_public_key=bytes(credencial.clave_publica),
            credential_current_sign_count=credencial.contador_firmas,
            require_user_verification=True,
        )
    except PasskeyError:
        raise
    except Exception as error:
        raise PasskeyError('No pudimos confirmar tu identidad. Inténtalo otra vez.') from error
    credencial.contador_firmas = verificado.new_sign_count
    credencial.ultimo_uso = timezone.now()
    credencial.save(update_fields=['contador_firmas', 'ultimo_uso'])
    return credencial


def usuario_por_rut(rut, tipos):
    return Usuario.objects.filter(rut=rut, is_active=True, tipo_usuario__in=tipos).first()
