"""
CC-19 · /api/token/ no puede ser un atajo para saltarse el segundo factor.

El token JWT se entrega solo con usuario y clave. Por eso:
- Al personal del CESFAM (que debe usar dos factores) no se le entrega token mientras el MFA
  esté activo: entra por la web, donde se pide la passkey.
- Cada intento fallido o rechazado queda en el registro de auditoría, y se aplica el mismo
  bloqueo de 5 claves incorrectas que en la pantalla de ingreso (OWASP A07).
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .. import personal, segundo_factor
from ..models import Usuario


class TokenSinAtajoSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        request = self.context.get('request')
        candidato = Usuario.objects.filter(username=attrs.get(self.username_field)).first()
        if candidato and candidato.es_personal and candidato.rut:
            # Misma regla que la web: bloqueo tras 5 claves y mensaje genérico
            try:
                personal.autenticar(request, candidato.rut, attrs.get('password', ''))
            except personal.PersonalError as error:
                raise serializers.ValidationError({'detail': str(error)})
            if segundo_factor.activo():
                raise serializers.ValidationError(
                    {'detail': 'El personal entra por la web con su clave y su dispositivo (dos factores).'})
        return super().validate(attrs)


class TokenSinAtajoView(TokenObtainPairView):
    serializer_class = TokenSinAtajoSerializer
