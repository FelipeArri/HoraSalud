from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CodigoEnrolamiento, Consentimiento, CredencialPasskey, SolicitudDerechos, Paciente, Profesional, Sector, Usuario


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


@admin.register(CredencialPasskey)
class CredencialPasskeyAdmin(admin.ModelAdmin):
    # Solo se ve la clave publica; no hay datos biometricos que mostrar
    list_display = ('usuario', 'dispositivo', 'creada_en', 'ultimo_uso')
    readonly_fields = ('usuario', 'credencial_id', 'contador_firmas', 'dispositivo', 'creada_en', 'ultimo_uso')
    exclude = ('clave_publica',)
    search_fields = ('usuario__rut',)

    def has_add_permission(self, request):
        return False


@admin.register(CodigoEnrolamiento)
class CodigoEnrolamientoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'creado_por', 'creado_en', 'expira_en', 'usado_en', 'intentos')
    readonly_fields = list_display
    exclude = ('codigo_hash',)

    def has_add_permission(self, request):
        return False


@admin.register(Consentimiento)
class ConsentimientoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'version', 'aceptado', 'fecha', 'retirado_en')
    list_filter = ('version', 'aceptado')
    readonly_fields = ('usuario', 'version', 'aceptado', 'fecha', 'retirado_en')

    def has_add_permission(self, request):
        return False  # solo lo registra la persona desde la app


@admin.register(SolicitudDerechos)
class SolicitudDerechosAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'estado', 'creada_en', 'resuelta_por')
    list_filter = ('tipo', 'estado')
