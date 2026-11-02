from django.contrib import admin

from .models import PersonaFonasa


@admin.register(PersonaFonasa)
class PersonaFonasaAdmin(admin.ModelAdmin):
    """Sección 'FONASA simulado' del panel: aquí se agregan personas de prueba."""
    list_display = ('rut', 'nombre_completo', 'prevision', 'tramo', 'estado_inscripcion', 'sector', 'caso')
    list_filter = ('prevision', 'estado_inscripcion', 'sector')
    search_fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno')
    fieldsets = (
        ('Persona', {'fields': ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'telefono')}),
        ('Previsión', {'fields': ('prevision', 'tramo')}),
        ('Inscripción en el CESFAM', {'fields': ('establecimiento', 'estado_inscripcion', 'sector')}),
        ('Para las pruebas', {'fields': ('caso',)}),
    )
