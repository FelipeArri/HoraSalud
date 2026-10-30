from django.contrib import admin

from .models import Agenda, BloqueHorario, Especialidad, Hora


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    list_filter = ('tipo',)


class BloqueEnLinea(admin.TabularInline):
    model = BloqueHorario
    extra = 0


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'especialidad', 'profesional')
    list_filter = ('especialidad', 'fecha')
    inlines = [BloqueEnLinea]


@admin.register(BloqueHorario)
class BloqueHorarioAdmin(admin.ModelAdmin):
    list_display = ('agenda', 'hora_inicio', 'hora_fin', 'estado')
    list_filter = ('estado', 'agenda__especialidad', 'agenda__fecha')


@admin.register(Hora)
class HoraAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'bloque', 'estado', 'creado_en')
    list_filter = ('estado', 'bloque__agenda__especialidad', 'bloque__agenda__fecha')
    search_fields = ('paciente__usuario__rut', 'paciente__usuario__last_name')
