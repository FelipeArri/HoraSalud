"""
B-20 · Precarga del personal y Excel LOCAL con sus cuentas de prueba.

Uso:
    python manage.py cargar_funcionarios

- Crea (si no existen) el Administrador CESFAM y un segundo funcionario SOME.
- Da una clave NUEVA al azar a todo el personal precargado: el Administrador, ese SOME
  y el personal demo de cargar_datos_demo (Sofía del SOME y los 3 profesionales).
- Escribe reportes/cuentas_personal.xlsx con RUT + clave. La carpeta reportes/ NO se
  sube a Git. Las claves se guardan en la base solo como hash: si pierdes el Excel,
  vuelve a ejecutar el comando (las claves cambian).

Los funcionarios que agregue el Administrador desde la app NO aparecen en el Excel:
su clave temporal se entrega en persona y solo se muestra una vez.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from autenticacionApp.models import Usuario
from autenticacionApp.personal import generar_clave
from autenticacionApp.validators import calcular_dv
from proyectoHoraSalud.excel import guardar_excel

PRECARGA = [  # RUT ficticios desde 32.000.000
    (32000001, 'Marcela', 'Ortiz Lagos', Usuario.Tipo.ADMINISTRADOR, 'Dirección CESFAM'),
    (32000002, 'Diego', 'Pérez Mella', Usuario.Tipo.ADMINISTRATIVO, 'SOME ventanilla'),
]
ARCHIVO = 'cuentas_personal.xlsx'


def personal_precargado():
    return (Usuario.objects.filter(tipo_usuario__in=Usuario.PERSONAL)
            .filter(username__regex=r'^(demo_|precarga_)')
            .select_related('profesional__especialidad').order_by('tipo_usuario', 'last_name'))


class Command(BaseCommand):
    help = 'Precarga el personal (incluido el Administrador CESFAM) y genera reportes/cuentas_personal.xlsx.'

    @transaction.atomic
    def handle(self, *args, **opciones):
        for numero, nombre, apellido, tipo, _ in PRECARGA:
            cuerpo = str(numero)
            Usuario.objects.get_or_create(username=f'precarga_{numero}', defaults={
                'rut': f'{cuerpo}-{calcular_dv(cuerpo)}', 'first_name': nombre, 'last_name': apellido,
                'tipo_usuario': tipo, 'email': f'{nombre.lower()}.{numero}@correo-ficticio.cl'})
        notas = {f'precarga_{n}': nota for n, *_, nota in PRECARGA}

        filas = []
        for usuario in personal_precargado():
            clave = generar_clave()
            usuario.set_password(clave)
            usuario.is_active = True
            usuario.debe_cambiar_clave = False  # cuentas de prueba: entran directo con la clave del Excel
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            usuario.save()
            prof = getattr(usuario, 'profesional', None)
            detalle = notas.get(usuario.username) or (str(prof.especialidad) if prof and prof.especialidad else '')
            filas.append([usuario.rut, clave, usuario.get_full_name(), usuario.get_tipo_usuario_display(), detalle])

        destino = guardar_excel(
            ARCHIVO, 'Cuentas del personal (precargadas)',
            f'SOLO PRUEBAS · datos ficticios · NO subir a Git ni compartir · generado {timezone.localtime():%d-%m-%Y %H:%M}',
            ['RUT', 'Clave', 'Nombre', 'Cargo', 'Detalle'], filas, [13, 16, 26, 22, 30])
        self.stdout.write(self.style.SUCCESS(f'{len(filas)} cuentas del personal con clave nueva. Excel: {destino}'))
        if not any(f[3] == 'Profesional' for f in filas):
            self.stdout.write('Aviso: no hay profesionales demo. Ejecuta antes: python manage.py cargar_datos_demo')
