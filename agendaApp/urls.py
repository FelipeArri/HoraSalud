from django.urls import path

from . import views, views_agendas as agendas

urlpatterns = [
    path('mi-inicio/', views.mi_inicio, name='mi_inicio'),
    path('ayuda/', views.ayuda, name='ayuda'),  # B-14: cómo funciona HoraSalud
    path('pedir-hora/', views.pedir_especialidad, name='pedir_especialidad'),
    path('pedir-hora/<int:especialidad_id>/', views.pedir_bloque, name='pedir_bloque'),
    path('pedir-hora/bloque/<int:bloque_id>/', views.pedir_confirmar, name='pedir_confirmar'),
    path('mis-horas/', views.mis_horas, name='mis_horas'),
    path('mis-horas/<uuid:hora_id>/', views.hora_lista, name='hora_lista'),
    path('mis-horas/<uuid:hora_id>/cancelar/', views.cancelar, name='cancelar_hora'),
    path('mis-horas/<uuid:hora_id>/confirmar/', views.confirmar_asistencia, name='confirmar_asistencia'),
    path('some/', views.some_nomina, name='some_nomina'),
    path('some/no-vigentes/', views.some_no_vigentes, name='some_no_vigentes'),
    # B-21 · gestión de agendas
    path('agendas/', agendas.semana, name='agendas_semana'),
    path('agendas/profesional/<uuid:profesional_id>/horario/', agendas.plantillas, name='agendas_plantillas'),
    path('agendas/horario/<int:plantilla_id>/estado/', agendas.plantilla_estado, name='agendas_plantilla_estado'),
    path('agendas/generar/', agendas.generar, name='agendas_generar'),
    path('agendas/duplicar/', agendas.duplicar, name='agendas_duplicar'),
    path('agendas/ausencias/', agendas.ausencias, name='agendas_ausencias'),
    path('some/ventanilla/', agendas.ventanilla, name='some_ventanilla'),
    path('profesional/control/<uuid:hora_id>/', agendas.proximo_control, name='profesional_control'),
    path('some/hora/<uuid:hora_id>/<str:accion>/', views.some_accion, name='some_accion'),
]
