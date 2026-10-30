from django.urls import path

from . import views

urlpatterns = [
    path('ingresar/', views.ingresar, name='ingresar'),
    path('ingresar/verificar/', views.verificar, name='verificar'),
    path('ingresar/a-cargo/', views.elegir_paciente, name='elegir_paciente'),
    path('salir/', views.salir, name='salir'),
    # Enrolamiento (B-06)
    path('activar-huella/', views.enrolar, name='enrolar'),
    path('activar-huella/registrar/', views.enrolar_huella, name='enrolar_huella'),
    path('some/enrolar/', views.some_enrolar, name='some_enrolar'),
    # Passkeys (WebAuthn): el navegador habla con estas rutas
    path('passkey/ingreso/opciones/', views.passkey_ingreso_opciones, name='passkey_ingreso_opciones'),
    path('passkey/ingreso/verificar/', views.passkey_ingreso_verificar, name='passkey_ingreso_verificar'),
    path('passkey/registro/opciones/', views.passkey_registro_opciones, name='passkey_registro_opciones'),
    path('passkey/registro/verificar/', views.passkey_registro_verificar, name='passkey_registro_verificar'),
]
