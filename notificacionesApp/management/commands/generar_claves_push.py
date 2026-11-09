"""B-14: crea el par de claves VAPID para los avisos push y las agrega al archivo .env.

Se ejecuta UNA vez por servidor:  python manage.py generar_claves_push
Si ya existen, no las cambia (cambiarlas obliga a todos a volver a activar los avisos).
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core.management.base import BaseCommand


def _b64(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b'=').decode()


class Command(BaseCommand):
    help = 'Genera las claves VAPID de los avisos push y las guarda en .env (B-14).'

    def handle(self, *args, **options):
        ruta = settings.BASE_DIR / '.env'
        actual = ruta.read_text(encoding='utf-8') if ruta.exists() else ''
        if 'VAPID_PRIVATE_KEY=' in actual and settings.VAPID_PRIVATE_KEY:
            self.stdout.write(self.style.WARNING('Las claves de avisos ya existen en .env: no se cambiaron.'))
            return
        privada = ec.generate_private_key(ec.SECP256R1())
        clave_privada = _b64(privada.private_numbers().private_value.to_bytes(32, 'big'))
        clave_publica = _b64(privada.public_key().public_bytes(serialization.Encoding.X962,
                                                               serialization.PublicFormat.UncompressedPoint))
        texto = ('\n# B-14: claves de los avisos push (generadas con manage.py generar_claves_push)\n'
                 f'VAPID_PUBLIC_KEY={clave_publica}\nVAPID_PRIVATE_KEY={clave_privada}\n')
        with ruta.open('a', encoding='utf-8') as archivo:
            archivo.write(texto)
        self.stdout.write(self.style.SUCCESS('Listo: claves agregadas a .env. Reinicia el servidor.'))
