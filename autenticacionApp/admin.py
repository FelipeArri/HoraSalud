from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Paciente, Profesional, Sector, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('rut', 'first_name', 'last_name', 'tipo_usuario', 'telefono', 'is_staff')
    list_filter = ('tipo_usuario', 'is_staff')
    search_fields = ('rut', 'first_name', 'last_name', 'username')
    fieldsets = UserAdmin.fieldsets + (('Datos HoraSalud', {'fields': ('rut', 'telefono', 'tipo_usuario')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Datos HoraSalud', {'fields': ('rut', 'tipo_usuario')}),)


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comuna')


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'sector', 'ficha_clinica_id', 'tutor')
    list_filter = ('sector',)
    search_fields = ('usuario__rut', 'usuario__first_name', 'usuario__last_name')


@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'especialidad', 'box_atencion')
    list_filter = ('especialidad',)
