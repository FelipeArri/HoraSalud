"""
B-14 · Envío real de avisos (RF-06, RNF-03) con costo cero.

Conecta el Factory Method + Strategy (notificacion_factory.py, estrategias.py)
con canales concretos, ambos GRATUITOS:
- PushStrategy -> PushGateway: aviso push (Web Push, estándar W3C). Lo entrega el
  servicio de notificaciones del navegador (en Android, el de Google), sin costo.
  Suena y vibra aunque la app esté cerrada.
- AvisoEnAppStrategy: el aviso se ve dentro de HoraSalud al entrar. Es también el
  respaldo si el push no llega. Para quien no usa la app, el SOME lo llama.

Privacidad (Ley 19.628): el texto del aviso pasa por servidores externos, por eso
nunca lleva datos de salud (ni especialidad, ni profesional, ni nombre).
"""
import json
import logging

from django.conf import settings
from django.utils import timezone

from autenticacionApp.models import Paciente

from .estrategias import AvisoEnAppStrategy, PushStrategy
from .models import RegistroNotificacion, SuscripcionPush
from .notificacion_factory import NotificacionFactory

logger = logging.getLogger(__name__)


def push_configurado():
    return bool(getattr(settings, 'VAPID_PRIVATE_KEY', '') and getattr(settings, 'VAPID_PUBLIC_KEY', ''))


def usuarios_a_avisar(paciente):
    """El paciente y, si tiene, su tutor (RF-03): ambos pueden aceptar el cupo."""
    usuarios = [paciente.usuario]
    if paciente.tutor_id:
        usuarios.append(paciente.tutor)
    return usuarios


def enviar_push(usuario, titulo, texto, url, ttl=600, etiqueta='horasalud'):
    """Envía el aviso a todos los dispositivos del usuario. Devuelve cuántos lo recibieron."""
    if not push_configurado():
        return 0
    from pywebpush import WebPushException, webpush
    datos = json.dumps({'titulo': titulo, 'texto': texto, 'url': url, 'etiqueta': etiqueta})
    entregados = 0
    for sus in SuscripcionPush.objects.filter(usuario=usuario):
        try:
            webpush(subscription_info={'endpoint': sus.endpoint, 'keys': {'p256dh': sus.p256dh, 'auth': sus.auth}},
                    data=datos, vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={'sub': settings.VAPID_CONTACTO}, ttl=ttl,
                    headers={'Urgency': 'high'}, timeout=8)
            entregados += 1
        except WebPushException as error:
            estado = getattr(error.response, 'status_code', None)
            if estado in (404, 410):  # el navegador dio de baja la suscripción
                sus.delete()
            logger.warning('Aviso push no entregado (%s): %s', estado, error)
        except Exception as error:  # sin internet, servicio caído: el aviso sigue visible en la app
            logger.warning('Aviso push no entregado: %s', error)
    return entregados


# ---------- Gateways concretos (lo que reciben las Strategy) ----------

class PushGateway:
    def __init__(self, url, ttl):
        self.url, self.ttl = url, ttl

    def enviar(self, usuario_id, texto):
        paciente = Paciente.objects.select_related('usuario', 'tutor').get(pk=usuario_id)
        total = sum(enviar_push(u, 'HoraSalud', texto, self.url, self.ttl) for u in usuarios_a_avisar(paciente))
        return total > 0


class RepositorioPacientes:
    """Arma los datos que el Factory Method usa para elegir el canal."""

    def buscar_por_id(self, paciente_id):
        paciente = Paciente.objects.select_related('usuario', 'tutor').get(pk=paciente_id)
        return {
            'id': paciente.pk,
            'app_instalada': SuscripcionPush.objects.filter(usuario__in=usuarios_a_avisar(paciente)).exists(),
        }


CANALES = {PushStrategy: RegistroNotificacion.Canal.PUSH, AvisoEnAppStrategy: RegistroNotificacion.Canal.APP}


def _registrar(paciente, canal, entregado, mensaje):
    estado = RegistroNotificacion.Estado.ENVIADA if entregado else RegistroNotificacion.Estado.FALLIDA
    return RegistroNotificacion.objects.create(paciente=paciente, canal=canal, estado=estado,
                                               mensaje=mensaje[:200], enviado_en=timezone.now())


def avisar(paciente, mensaje, url='/lista-espera/', ttl=600):
    """Envía el aviso por el canal que corresponda (gratis) y lo deja registrado. Devuelve el registro."""
    factory = NotificacionFactory(RepositorioPacientes(), PushGateway(url, ttl))
    notificacion = factory.crear_notificacion(paciente_id=paciente.pk, hora_id=None, mensaje=mensaje)
    try:
        entregado = notificacion.enviar()
    except Exception as error:
        logger.warning('No se pudo enviar el aviso: %s', error)
        entregado = False
    registro = _registrar(paciente, CANALES[type(notificacion.estrategia)], entregado, mensaje)
    if not entregado:
        # Respaldo: si el push no llegó, el aviso igual queda visible dentro de HoraSalud
        registro = _registrar(paciente, RegistroNotificacion.Canal.APP, AvisoEnAppStrategy().enviar(mensaje, {}),
                              mensaje)
    return registro
