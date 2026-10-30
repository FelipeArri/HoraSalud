from django.contrib import admin

from .models import RegistroNotificacion


@admin.register(RegistroNotificacion)
class RegistroNotificacionAdmin(admin.ModelAdmin):
    list_display = ('hora', 'canal', 'estado', 'enviado_en')
    list_filter = ('canal', 'estado')
