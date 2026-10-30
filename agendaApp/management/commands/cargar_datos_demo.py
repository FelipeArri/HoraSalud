"""
Carga datos FICTICIOS para probar HoraSalud: sectores, especialidades,
profesionales, pacientes, tutores, agendas de los proximos 5 dias habiles,
horas reservadas y lista de espera.

Uso:
    python manage.py cargar_datos_demo            # carga (no duplica)
    python manage.py cargar_datos_demo --limpiar  # borra los datos demo y vuelve a cargar

Ningun dato corresponde a una persona real (Ley 21.719, Ley 20.584).
Los usuarios demo no tienen contrasena: ingresaran con passkey (Sprint 4).
"""
import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from agendaApp.models import Agenda, BloqueHorario, Especialidad, Hora
from autenticacionApp.models import Paciente, Profesional, Sector
from autenticacionApp.validators import calcular_dv
from listaEsperaApp.models import EsperaPaciente

Usuario = get_user_model()
PREFIJO = 'demo_'

SECTORES = ['Sector 1', 'Sector 2', 'Sector 3']
ESPECIALIDADES = [
    ('Medicina General', Especialidad.Tipo.MEDICINA_GENERAL),
    ('Control Cronico - Diabetes', Especialidad.Tipo.PROGRAMA),
    ('Matroneria', Especialidad.Tipo.PROGRAMA),
]
PROFESIONALES = [('Valentina', 'Rojas Soto', 0, 'B-01'), ('Matias', 'Fuentes Lagos', 1, 'B-02'),
                 ('Camila', 'Navarro Pino', 2, 'B-03')]
TUTORES = [('Patricia', 'Morales Vega'), ('Jorge', 'Castillo Ruiz')]
PACIENTES = [('Rosa', 'Gonzalez Mena'), ('Luis', 'Herrera Diaz'), ('Carmen', 'Silva Araya'),
             ('Pedro', 'Munoz Tapia'), ('Elena', 'Contreras Paz'), ('Manuel', 'Vargas Reyes'),
             ('Teresa', 'Espinoza Leiva'), ('Hector', 'Pizarro Olivares'), ('Gloria', 'Saavedra Nunez'),
             ('Raul', 'Carrasco Bravo'), ('Ines', 'Sepulveda Toro'), ('Oscar', 'Alarcon Mella')]
DURACION_BLOQUE_MIN = 20


def rut_ficticio(numero):
    cuerpo = str(numero)
    return f'{cuerpo}-{calcular_dv(cuerpo)}'


def proximos_dias_habiles(cantidad):
    dia, dias = date.today(), []
    while len(dias) < cantidad:
        dia += timedelta(days=1)
        if dia.weekday() < 5:
            dias.append(dia)
    return dias


class Command(BaseCommand):
    help = 'Carga datos ficticios de prueba (no usar con datos reales).'

    def add_arguments(self, parser):
        parser.add_argument('--limpiar', action='store_true', help='Borra los datos demo antes de cargar.')

    @transaction.atomic
    def handle(self, *args, **opciones):
        if opciones['limpiar']:
            self._limpiar()

        sectores = [Sector.objects.get_or_create(nombre=n, comuna='La Granja')[0] for n in SECTORES]
        especialidades = [Especialidad.objects.get_or_create(nombre=n, tipo=t)[0] for n, t in ESPECIALIDADES]

        numero = 30000000  # RUT ficticios desde 30.000.000
        profesionales = []
        for nombre, apellido, i_esp, box in PROFESIONALES:
            numero += 1
            usuario = self._usuario(numero, nombre, apellido, Usuario.Tipo.PROFESIONAL)
            prof, _ = Profesional.objects.get_or_create(usuario=usuario, defaults={
                'especialidad': especialidades[i_esp], 'box_atencion': box})
            profesionales.append(prof)

        numero += 1
        self._usuario(numero, 'Sofia', 'Ramirez Cortes', Usuario.Tipo.ADMINISTRATIVO)

        tutores = []
        for nombre, apellido in TUTORES:
            numero += 1
            tutores.append(self._usuario(numero, nombre, apellido, Usuario.Tipo.TUTOR))

        pacientes = []
        for i, (nombre, apellido) in enumerate(PACIENTES):
            numero += 1
            usuario = self._usuario(numero, nombre, apellido, Usuario.Tipo.PACIENTE)
            paciente, _ = Paciente.objects.get_or_create(usuario=usuario, defaults={
                'sector': sectores[i % 3],
                'ficha_clinica_id': f'FC-{1000 + i}',
                'tutor': tutores[i] if i < len(tutores) else None,  # RF-03: dos pacientes con tutor
            })
            pacientes.append(paciente)

        bloques = []
        for dia in proximos_dias_habiles(5):
            for prof in profesionales:
                agenda, _ = Agenda.objects.get_or_create(especialidad=prof.especialidad, profesional=prof, fecha=dia)
                inicio = datetime.combine(dia, time(8, 0))
                while inicio.time() < time(12, 0):
                    fin = inicio + timedelta(minutes=DURACION_BLOQUE_MIN)
                    bloque, _ = BloqueHorario.objects.get_or_create(
                        agenda=agenda, hora_inicio=inicio.time(), defaults={'hora_fin': fin.time()})
                    bloques.append(bloque)
                    inicio = fin

        if not Hora.objects.filter(paciente__usuario__username__startswith=PREFIJO).exists():
            azar = random.Random(7)  # siempre los mismos datos
            disponibles = [b for b in bloques if b.estado == BloqueHorario.Estado.DISPONIBLE]
            estados = [Hora.Estado.RESERVADA] * 8 + [Hora.Estado.CONFIRMADA] * 5 + [Hora.Estado.CANCELADA] * 2
            for paciente, estado in zip(pacientes + pacientes[:3], estados):
                bloque = disponibles.pop(azar.randrange(len(disponibles)))
                Hora.objects.create(bloque=bloque, paciente=paciente, estado=estado,
                                    motivo_cancelacion='Paciente avisa que no puede asistir'
                                    if estado == Hora.Estado.CANCELADA else '')
                if estado != Hora.Estado.CANCELADA:
                    bloque.estado = BloqueHorario.Estado.RESERVADO
                    bloque.save()

        for orden, paciente in enumerate(pacientes[-3:], start=1):
            EsperaPaciente.objects.get_or_create(especialidad=especialidades[0], paciente=paciente,
                                                 defaults={'orden': orden})

        self.stdout.write(self.style.SUCCESS(
            f'Datos demo listos: {Usuario.objects.filter(username__startswith=PREFIJO).count()} usuarios, '
            f'{Paciente.objects.count()} pacientes, {Agenda.objects.count()} agendas, '
            f'{BloqueHorario.objects.count()} bloques, {Hora.objects.count()} horas, '
            f'{EsperaPaciente.objects.count()} en lista de espera.'))

    def _usuario(self, numero, nombre, apellido, tipo):
        rut = rut_ficticio(numero)
        usuario, creado = Usuario.objects.get_or_create(username=f'{PREFIJO}{numero}', defaults={
            'rut': rut, 'first_name': nombre, 'last_name': apellido, 'tipo_usuario': tipo,
            'email': f'{nombre.lower()}.{numero}@correo-ficticio.cl', 'telefono': f'+5690000{numero % 10000:04d}',
        })
        if creado:
            usuario.set_unusable_password()
            usuario.save()
        return usuario

    def _limpiar(self):
        demo = Usuario.objects.filter(username__startswith=PREFIJO)
        EsperaPaciente.objects.filter(paciente__usuario__in=demo).delete()
        Hora.objects.filter(paciente__usuario__in=demo).delete()
        Agenda.objects.filter(profesional__usuario__in=demo).delete()
        Paciente.objects.filter(usuario__in=demo).delete()
        Profesional.objects.filter(usuario__in=demo).delete()
        demo.delete()
        self.stdout.write('Datos demo anteriores borrados.')
