"""B-07: cifra los motivos de cancelacion que ya estaban guardados en texto plano."""
from django.db import migrations


def cifrar_existentes(apps, schema_editor):
    Hora = apps.get_model('agendaApp', 'Hora')
    for hora in Hora.objects.exclude(motivo_cancelacion=''):
        hora.save(update_fields=['motivo_cancelacion'])


class Migration(migrations.Migration):
    dependencies = [('agendaApp', '0003_consentimiento_y_cifrado')]
    operations = [migrations.RunPython(cifrar_existentes, migrations.RunPython.noop)]
