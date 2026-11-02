"""
Padron inicial de FONASA simulado: 25 personas FICTICIAS con todos los casos de prueba.
Se pueden agregar mas desde /admin/ → "Padrón FONASA simulado".
"""
from django.db import migrations

CESFAM = 'CESFAM Padre Esteban Gumucio'


def dv(cuerpo):
    suma, factor = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: '0', 10: 'K'}.get(resto, str(resto))


# (numero, nombres, paterno, materno, prevision, tramo, inscripcion, establecimiento, sector, telefono, caso)
DEMO = [('Rosa', 'Gonzalez', 'Mena'), ('Luis', 'Herrera', 'Diaz'), ('Carmen', 'Silva', 'Araya'),
        ('Pedro', 'Munoz', 'Tapia'), ('Elena', 'Contreras', 'Paz'), ('Manuel', 'Vargas', 'Reyes'),
        ('Teresa', 'Espinoza', 'Leiva'), ('Hector', 'Pizarro', 'Olivares'), ('Gloria', 'Saavedra', 'Nunez'),
        ('Raul', 'Carrasco', 'Bravo'), ('Ines', 'Sepulveda', 'Toro'), ('Oscar', 'Alarcon', 'Mella')]

PERSONAS = [
    (30000007 + i, n, p, m, 'FONASA', 'ABCD'[i % 4], 'ACTIVA', CESFAM, f'SECTOR {i % 3 + 1}', '',
     'Paciente de los datos demo (cargar_datos_demo)')
    for i, (n, p, m) in enumerate(DEMO)
] + [
    (31000001, 'Ana María', 'Prueba', 'Ficticia', 'FONASA', 'B', 'ACTIVA', CESFAM, 'SECTOR 2', '+56911112222',
     'Persona nueva con FONASA B: recibe código'),
    (31000002, 'Bruno', 'Isapre', 'Ficticio', 'ISAPRE', '', 'ACTIVA', CESFAM, 'SECTOR 1', '',
     'Tiene ISAPRE: no pertenece al consultorio'),
    (31000003, 'Carla', 'Dipreca', 'Ficticia', 'DIPRECA', '', 'ACTIVA', CESFAM, 'SECTOR 3', '',
     'Tiene DIPRECA: no pertenece al consultorio'),
    (31000004, 'Daniel', 'Capredena', 'Ficticio', 'CAPREDENA', '', 'ACTIVA', CESFAM, 'SECTOR 2', '',
     'Tiene CAPREDENA: no pertenece al consultorio'),
    (31000005, 'Eva', 'Sinprevision', 'Ficticia', 'SIN_PREVISION', '', 'ACTIVA', CESFAM, 'SECTOR 1', '',
     'Sin previsión: orientar a postular como carente de recursos'),
    (31000006, 'Fernando', 'Noinscrito', 'Ficticio', 'FONASA', 'A', 'NO_INSCRITO', CESFAM, '', '',
     'Tiene FONASA pero no está inscrito en el CESFAM'),
    (31000007, 'Gabriel', 'Traslado', 'Ficticio', 'FONASA', 'C', 'PASIVA', CESFAM, 'SECTOR 2', '',
     'Inscripción pasiva: se trasladó a otro CESFAM'),
    (31000008, 'Hilda', 'Mayor', 'Ficticia', 'FONASA', 'A', 'ACTIVA', CESFAM, 'SECTOR 1', '+56922223333',
     'Persona nueva, adulta mayor (82 años): ideal para probar con tutor'),
    (31000009, 'Ignacio', 'Nuevo', 'Ficticio', 'FONASA', 'D', 'ACTIVA', CESFAM, 'SECTOR 3', '',
     'Persona nueva con FONASA D'),
    (31000010, 'Julia', 'Nueva', 'Ficticia', 'FONASA', 'C', 'ACTIVA', CESFAM, 'SECTOR 2', '+56933334444',
     'Persona nueva con FONASA C'),
    (31000011, 'Kevin', 'Nuevo', 'Ficticio', 'FONASA', 'B', 'ACTIVA', CESFAM, 'SECTOR 1', '',
     'Persona nueva con FONASA B'),
    (31000012, 'Laura', 'Nueva', 'Ficticia', 'FONASA', 'A', 'ACTIVA', CESFAM, 'SECTOR 3', '+56944445555',
     'Persona nueva: útil para probar la huella en el celular'),
    (31000013, 'Mario', 'Otrocesfam', 'Ficticio', 'FONASA', 'B', 'ACTIVA', 'CESFAM Santa Anselma', 'SECTOR 1', '',
     'Inscrito en OTRO CESFAM: no corresponde a este'),
]


def cargar(apps, schema_editor):
    Persona = apps.get_model('fonasaSimuladoApp', 'PersonaFonasa')
    base = schema_editor.connection.alias
    for numero, nombres, paterno, materno, prev, tramo, insc, estab, sector, fono, caso in PERSONAS:
        Persona.objects.using(base).update_or_create(rut=f'{numero}-{dv(numero)}', defaults={
            'nombres': nombres, 'apellido_paterno': paterno, 'apellido_materno': materno, 'prevision': prev,
            'tramo': tramo, 'estado_inscripcion': insc, 'establecimiento': estab, 'sector': sector,
            'telefono': fono, 'caso': caso})


def quitar(apps, schema_editor):
    Persona = apps.get_model('fonasaSimuladoApp', 'PersonaFonasa')
    ruts = [f'{n}-{dv(n)}' for n, *_ in PERSONAS]
    Persona.objects.using(schema_editor.connection.alias).filter(rut__in=ruts).delete()


class Migration(migrations.Migration):
    dependencies = [('fonasaSimuladoApp', '0001_initial')]
    operations = [migrations.RunPython(cargar, quitar)]
