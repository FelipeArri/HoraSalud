from django.contrib import admin

from .models import EsperaPaciente


@admin.register(EsperaPaciente)
class EsperaPacienteAdmin(admin.ModelAdmin):
    list_display = ('orden', 'paciente', 'especialidad', 'creado_en')
    list_filter = ('especialidad',)
