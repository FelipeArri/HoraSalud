"""Rutas principales de HoraSalud: reparten hacia cada aplicacion."""
from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .salud import salud


class IconoView(RedirectView):
    """El navegador pide /favicon.ico por su cuenta: se envía al icono en static.
    La dirección se calcula en cada visita (B-16: en producción el nombre lleva versión)."""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return static('images/favicon.ico')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', IconoView.as_view()),
    # API
    path('api/salud/', salud, name='api_salud'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Paginas
    path('', include('pantallaApp.urls')),
    path('', include('autenticacionApp.urls')),
    path('', include('agendaApp.urls')),
    path('', include('listaEsperaApp.urls')),  # B-14
    path('', include('notificacionesApp.urls')),  # B-14: app instalable y avisos push
]
