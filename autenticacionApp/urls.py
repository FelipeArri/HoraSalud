from django.urls import path

from . import views

urlpatterns = [
    path('ingresar/', views.ingresar, name='ingresar'),
    path('ingresar/verificar/', views.verificar, name='verificar'),
    path('ingresar/a-cargo/', views.elegir_paciente, name='elegir_paciente'),
    path('salir/', views.salir, name='salir'),
]
