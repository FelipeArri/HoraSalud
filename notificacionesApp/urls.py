from django.urls import path

from . import views

urlpatterns = [
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('sin-conexion/', views.sin_conexion, name='sin_conexion'),
    path('avisos/suscribir/', views.suscribir, name='avisos_suscribir'),
    path('avisos/quitar/', views.quitar, name='avisos_quitar'),
    path('avisos/prueba/', views.prueba, name='avisos_prueba'),
]
