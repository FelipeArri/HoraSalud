from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('pantalla/', views.sala_espera, name='sala_espera'),
]
