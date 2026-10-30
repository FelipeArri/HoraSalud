"""Validacion del RUT chileno (RF-01)."""
import re

from django.core.exceptions import ValidationError

FORMATO_RUT = re.compile(r'^\d{7,8}-[\dK]$')


def calcular_dv(cuerpo):
    """Calcula el digito verificador de un RUT con el algoritmo modulo 11."""
    suma, factor = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: '0', 10: 'K'}.get(resto, str(resto))


def normalizar_rut(rut):
    """Deja el RUT como 12345678-9: sin puntos ni espacios y con K mayuscula."""
    return str(rut).replace('.', '').replace(' ', '').upper()


def validar_rut(rut):
    """RF-01: rechaza formato invalido o digito verificador incorrecto."""
    rut = normalizar_rut(rut)
    if not FORMATO_RUT.match(rut):
        raise ValidationError('El RUT debe tener el formato 12345678-9.')
    cuerpo, dv = rut.split('-')
    if calcular_dv(cuerpo) != dv:
        raise ValidationError('El digito verificador del RUT no es valido.')
