from django.urls import path

from . import views

urlpatterns = [
    path('lista-espera/', views.mi_lista, name='mi_lista_espera'),
    path('lista-espera/inscribirme/<int:especialidad_id>/', views.inscribirme, name='inscribirme_lista'),
    path('lista-espera/<int:espera_id>/salir/', views.salir_de_lista, name='salir_lista'),
    path('lista-espera/oferta/<uuid:oferta_id>/', views.oferta, name='oferta_cupo'),
    path('some/lista-espera/', views.some_lista, name='some_lista_espera'),
    path('some/lista-espera/<int:espera_id>/quitar/', views.some_quitar, name='some_quitar_lista'),
    path('some/lista-espera/oferta/<uuid:oferta_id>/<str:accion>/', views.some_oferta, name='some_oferta'),
    path('personal/lista-espera/indicadores/', views.indicadores, name='indicadores_lista'),
]
