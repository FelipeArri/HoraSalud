from django.urls import path

from . import views, views_privacidad as privacidad

urlpatterns = [
    path('ingresar/', views.ingresar, name='ingresar'),
    path('ingresar/verificar/', views.verificar, name='verificar'),
    path('ingresar/a-cargo/', views.elegir_paciente, name='elegir_paciente'),
    path('salir/', views.salir, name='salir'),
    # Enrolamiento (B-06)
    path('activar-huella/', views.enrolar, name='enrolar'),
    path('activar-huella/privacidad/', privacidad.enrolar_consentimiento, name='enrolar_consentimiento'),
    path('activar-huella/registrar/', views.enrolar_huella, name='enrolar_huella'),
    path('some/enrolar/', views.some_enrolar, name='some_enrolar'),
    # Passkeys (WebAuthn): el navegador habla con estas rutas
    path('passkey/ingreso/opciones/', views.passkey_ingreso_opciones, name='passkey_ingreso_opciones'),
    path('passkey/ingreso/verificar/', views.passkey_ingreso_verificar, name='passkey_ingreso_verificar'),
    path('passkey/registro/opciones/', views.passkey_registro_opciones, name='passkey_registro_opciones'),
    path('passkey/registro/verificar/', views.passkey_registro_verificar, name='passkey_registro_verificar'),
    # Privacidad y derechos ARCO+ (B-07, Ley 21.719)
    path('privacidad/', privacidad.politica, name='politica'),
    path('privacidad/aceptar/', privacidad.aceptar_politica, name='aceptar_politica'),
    path('mis-datos/', privacidad.mis_datos, name='mis_datos'),
    path('mis-datos/descargar/', privacidad.descargar_mis_datos, name='descargar_mis_datos'),
    path('mis-datos/dispositivo/<int:passkey_id>/borrar/', privacidad.borrar_dispositivo, name='borrar_dispositivo'),
    path('mis-datos/solicitud/', privacidad.solicitar_derecho, name='solicitar_derecho'),
    path('mis-datos/retirar/', privacidad.retirar_consentimiento, name='retirar_consentimiento'),
    path('some/solicitudes/', privacidad.some_solicitudes, name='some_solicitudes'),
]
