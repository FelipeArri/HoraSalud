"""Rutas principales de HoraSalud: reparten hacia cada aplicacion."""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .salud import salud

urlpatterns = [
    path('admin/', admin.site.urls),
    # API
    path('api/salud/', salud, name='api_salud'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Paginas
    path('', include('pantallaApp.urls')),
]
