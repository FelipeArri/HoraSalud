from django.urls import path

from . import views

urlpatterns = [
    path('mi-inicio/', views.mi_inicio, name='mi_inicio'),
    path('pedir-hora/', views.pedir_especialidad, name='pedir_especialidad'),
    path('pedir-hora/<int:especialidad_id>/', views.pedir_bloque, name='pedir_bloque'),
    path('pedir-hora/bloque/<int:bloque_id>/', views.pedir_confirmar, name='pedir_confirmar'),
    path('mis-horas/', views.mis_horas, name='mis_horas'),
    path('mis-horas/<uuid:hora_id>/', views.hora_lista, name='hora_lista'),
    path('mis-horas/<uuid:hora_id>/cancelar/', views.cancelar, name='cancelar_hora'),
    path('mis-horas/<uuid:hora_id>/confirmar/', views.confirmar_asistencia, name='confirmar_asistencia'),
    path('some/', views.some_nomina, name='some_nomina'),
    path('some/hora/<uuid:hora_id>/<str:accion>/', views.some_accion, name='some_accion'),
]
