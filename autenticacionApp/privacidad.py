"""
B-07 · Consentimiento y derechos ARCO+ (Ley 21.719).

VERSION_POLITICA: si cambia el texto de la politica (templates/autenticacionApp/
_politica.html), se sube la version y el sistema vuelve a pedir la aceptacion.
"""
from django.utils import timezone

from .models import Consentimiento

VERSION_POLITICA = '1.0'


def consentimiento_vigente(usuario):
    """True si aceptó la versión actual y no la ha retirado."""
    ultimo = usuario.consentimientos.filter(version=VERSION_POLITICA).first()
    return bool(ultimo and ultimo.aceptado and not ultimo.retirado_en)


def registrar(usuario, aceptado):
    return Consentimiento.objects.create(usuario=usuario, version=VERSION_POLITICA, aceptado=aceptado)


def retirar(usuario):
    usuario.consentimientos.filter(aceptado=True, retirado_en__isnull=True).update(retirado_en=timezone.now())


def exportar_datos(usuario):
    """Derecho de acceso y portabilidad: todo lo que HoraSalud guarda de la persona, en un formato estándar."""
    datos = {
        'generado_en': timezone.localtime().isoformat(),
        'responsable': 'CESFAM Padre Esteban Gumucio (prototipo académico HoraSalud)',
        'persona': {
            'rut': usuario.rut, 'nombres': usuario.first_name, 'apellidos': usuario.last_name,
            'telefono': usuario.telefono, 'correo': usuario.email, 'tipo': usuario.get_tipo_usuario_display(),
        },
        'consentimientos': [
            {'version': c.version, 'aceptado': c.aceptado, 'fecha': c.fecha.isoformat(),
             'retirado_en': c.retirado_en.isoformat() if c.retirado_en else None}
            for c in usuario.consentimientos.all()],
        'dispositivos_con_huella': [
            {'dispositivo': p.dispositivo, 'dominio': p.rp_id, 'creado': p.creada_en.isoformat(),
             'ultimo_uso': p.ultimo_uso.isoformat() if p.ultimo_uso else None}
            for p in usuario.passkeys.all()],
        'solicitudes': [
            {'tipo': s.get_tipo_display(), 'estado': s.get_estado_display(), 'fecha': s.creada_en.isoformat()}
            for s in usuario.solicitudes_derechos.all()],
        'nota': 'La huella o el rostro nunca se guardan en HoraSalud: quedan en tu dispositivo.',
    }
    paciente = getattr(usuario, 'paciente', None)
    if paciente:
        datos['paciente'] = {
            'sector': str(paciente.sector) if paciente.sector else None,
            'ficha_clinica': paciente.ficha_clinica_id,
            'tutor': str(paciente.tutor) if paciente.tutor else None,
            'horas': [
                {'fecha': h.bloque.agenda.fecha.isoformat(), 'hora': h.bloque.hora_inicio.strftime('%H:%M'),
                 'atencion': h.bloque.agenda.especialidad.nombre, 'estado': h.get_estado_display(),
                 'motivo_cancelacion': h.motivo_cancelacion or None}
                for h in paciente.horas.select_related('bloque__agenda__especialidad')],
        }
    return datos
