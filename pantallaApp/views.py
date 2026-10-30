from django.shortcuts import render


def inicio(request):
    """Pagina de inicio de HoraSalud."""
    return render(request, 'pantallaApp/inicio.html')
