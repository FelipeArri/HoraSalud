"""
Autenticador simulado SOLO PARA PRUEBAS AUTOMATICAS.

Hace lo mismo que el chip seguro del telefono o Windows Hello: crea un par de
claves (ECDSA P-256), entrega la clave publica al registrarse y firma el reto
al ingresar. Permite probar la verificacion criptografica real de py_webauthn
sin un dispositivo fisico.
"""
import hashlib
import json
import os
import struct

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

FLAG_PRESENCIA, FLAG_VERIFICACION, FLAG_CREDENCIAL = 0x01, 0x04, 0x40


class AutenticadorSimulado:
    def __init__(self, rp_id='localhost', origen='http://localhost:8000', verifica_usuario=True):
        self.rp_id = rp_id
        self.origen = origen
        self.verifica_usuario = verifica_usuario
        self.clave = ec.generate_private_key(ec.SECP256R1())
        self.credencial_id = os.urandom(32)
        self.contador = 0

    def _flags(self, extra=0):
        flags = FLAG_PRESENCIA | extra
        return flags | FLAG_VERIFICACION if self.verifica_usuario else flags

    def _auth_data(self, flags, adjunto=b''):
        self.contador += 1
        return hashlib.sha256(self.rp_id.encode()).digest() + bytes([flags]) + struct.pack('>I', self.contador) + adjunto

    def _client_data(self, tipo, reto_b64):
        return json.dumps({'type': tipo, 'challenge': reto_b64, 'origin': self.origen,
                           'crossOrigin': False}).encode()

    def registrar(self, opciones_json):
        opciones = json.loads(opciones_json)
        numeros = self.clave.public_key().public_numbers()
        cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: numeros.x.to_bytes(32, 'big'), -3: numeros.y.to_bytes(32, 'big')})
        adjunto = bytes(16) + struct.pack('>H', len(self.credencial_id)) + self.credencial_id + cose
        auth_data = self._auth_data(self._flags(FLAG_CREDENCIAL), adjunto)
        client_data = self._client_data('webauthn.create', opciones['challenge'])
        id_b64 = bytes_to_base64url(self.credencial_id)
        return json.dumps({
            'id': id_b64, 'rawId': id_b64, 'type': 'public-key',
            'response': {
                'clientDataJSON': bytes_to_base64url(client_data),
                'attestationObject': bytes_to_base64url(cbor2.dumps({'fmt': 'none', 'attStmt': {}, 'authData': auth_data})),
                'transports': ['internal'],
            },
            'authenticatorAttachment': 'platform', 'clientExtensionResults': {},
        })

    def firmar(self, opciones_json, user_handle=b''):
        opciones = json.loads(opciones_json)
        auth_data = self._auth_data(self._flags())
        client_data = self._client_data('webauthn.get', opciones['challenge'])
        firma = self.clave.sign(auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256()))
        id_b64 = bytes_to_base64url(self.credencial_id)
        return json.dumps({
            'id': id_b64, 'rawId': id_b64, 'type': 'public-key',
            'response': {
                'clientDataJSON': bytes_to_base64url(client_data),
                'authenticatorData': bytes_to_base64url(auth_data),
                'signature': bytes_to_base64url(firma),
                'userHandle': bytes_to_base64url(user_handle) if user_handle else None,
            },
            'authenticatorAttachment': 'platform', 'clientExtensionResults': {},
        })


__all__ = ['AutenticadorSimulado', 'base64url_to_bytes']
