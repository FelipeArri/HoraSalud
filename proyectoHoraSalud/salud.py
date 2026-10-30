"""Ruta de salud: prueba de humo del despliegue (D33-C07, paso 5)."""
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def salud(request):
    """Indica si la API y la base de datos responden. No expone datos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return Response({'api': 'ok', 'baseDatos': 'ok'})
    except Exception:
        # OWASP A05: no se muestra el detalle del error al cliente.
        return Response({'api': 'ok', 'baseDatos': 'sin conexion'}, status=503)
