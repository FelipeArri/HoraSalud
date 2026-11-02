"""
Cifrado de campos sensibles en reposo (B-07, RNF-SEC02, Ley 21.719).

`CampoCifrado` guarda el valor cifrado en la base de datos (Fernet: AES-128 +
HMAC) y lo entrega descifrado al codigo. Si alguien copia la base sin la clave
HORASALUD_CLAVE_CIFRADO, solo ve texto ilegible.

Se usa en datos que no sirven para buscar: telefono y motivos de cancelacion.
El RUT no se cifra porque es la llave de busqueda; se protege con control de
acceso y auditoria.
"""
import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

PREFIJO = 'enc:'  # marca para distinguir un valor cifrado de uno antiguo en texto plano
NO_DESCIFRABLE = '(dato cifrado con otra clave)'


@lru_cache(maxsize=1)
def _fernet():
    clave = settings.HORASALUD_CLAVE_CIFRADO
    if not clave:
        # Solo en desarrollo: clave derivada de SECRET_KEY (ver settings)
        clave = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()).decode()
    return Fernet(clave.encode() if isinstance(clave, str) else clave)


def cifrar(texto):
    if not texto:
        return texto
    return PREFIJO + _fernet().encrypt(str(texto).encode()).decode()


def descifrar(valor):
    if not valor or not str(valor).startswith(PREFIJO):
        return valor  # vacio o dato antiguo sin cifrar
    try:
        return _fernet().decrypt(valor[len(PREFIJO):].encode()).decode()
    except InvalidToken:
        return NO_DESCIFRABLE


class CampoCifrado(models.TextField):
    """Texto que se guarda cifrado. En formularios se ve como un campo de una linea."""

    def __init__(self, *args, largo_maximo=None, **kwargs):
        self.largo_maximo = largo_maximo
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        nombre, ruta, args, kwargs = super().deconstruct()
        if self.largo_maximo:
            kwargs['largo_maximo'] = self.largo_maximo
        return nombre, ruta, args, kwargs

    def from_db_value(self, valor, expression, connection):
        return descifrar(valor)

    def to_python(self, valor):
        return descifrar(valor) if isinstance(valor, str) else valor

    def get_prep_value(self, valor):
        valor = super().get_prep_value(valor)
        if valor and str(valor).startswith(PREFIJO):
            return valor  # ya viene cifrado
        return cifrar(valor)

    def formfield(self, **kwargs):
        from django import forms
        kwargs.setdefault('widget', forms.TextInput)
        kwargs.setdefault('max_length', self.largo_maximo)
        return super().formfield(**kwargs)
