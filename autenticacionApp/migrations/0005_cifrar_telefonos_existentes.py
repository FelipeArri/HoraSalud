"""B-07: cifra los telefonos que ya estaban guardados en texto plano."""
from django.db import migrations


def cifrar_existentes(apps, schema_editor):
    Usuario = apps.get_model('autenticacionApp', 'Usuario')
    for usuario in Usuario.objects.exclude(telefono=''):
        # Al volver a guardar, CampoCifrado cifra el valor (los ya cifrados no cambian)
        usuario.save(update_fields=['telefono'])


class Migration(migrations.Migration):
    dependencies = [('autenticacionApp', '0004_consentimiento_y_cifrado')]
    operations = [migrations.RunPython(cifrar_existentes, migrations.RunPython.noop)]
