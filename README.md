# HoraSalud

Sistema de agendamiento de horas del CESFAM Padre Esteban Gumucio (La Granja).
Proyecto semestral de Ingeniería de Software (TI3043), INACAP.
Equipo: Felipe Arriaza y Cristian Plaza.

Django 4.2 · Django REST Framework · JWT · MySQL/MariaDB (XAMPP) · Bootstrap

> Todos los datos de este repositorio son **ficticios**. Nunca se cargan datos
> reales de pacientes (Ley 21.719 y Ley 20.584).

## Mapa del proyecto

| Carpeta o archivo | Qué es | Requisitos |
|---|---|---|
| `manage.py` | Programa con que se ejecutan los comandos de Django | — |
| `proyectoHoraSalud\settings.py` | Configuración global (lee el `.env`) | RNF-SEC02 |
| `proyectoHoraSalud\urls.py` | Rutas principales; reparte hacia cada aplicación | — |
| `proyectoHoraSalud\salud.py` | Ruta `/api/salud/`, prueba de humo | D33-C07 |
| `proyectoHoraSalud\configuracion_sistema.py` | Parámetros del negocio (Singleton) | RN-03, RF-05 |
| `autenticacionApp\` | RUT, enrolamiento, passkeys y tutor (Adapter) | RF-01, RF-03 |
| `agendaApp\` | Horas, reservas y No-Show (Command) | RF-02, RF-04, RF-05 |
| `listaEsperaApp\` | Lista de espera (Observer) | RF-06 |
| `notificacionesApp\` | Avisos al paciente (Factory Method + Strategy) | RNF-03 |
| `pantallaApp\` | Inicio y pantalla de la sala de espera | — |
| `<app>\api\` | API de cada aplicación: serializers, views, urls | — |
| `templates\` | Páginas HTML, una carpeta por aplicación | D23-C03 |
| `static\` | CSS, imágenes y Bootstrap | RNF-03 |
| `.env` | Credenciales, fuera del repositorio | RNF-SEC02 |
| `requirements.txt` | Librerías y versiones del proyecto | — |
| `docs\` | Guías por sprint y plan de sprints | D42-C04 |

## Cómo levantarlo (resumen)

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # y completar los valores
python manage.py migrate
python manage.py test
python manage.py runserver
```

La guía paso a paso está en [docs/GUIA_SPRINT_3.md](docs/GUIA_SPRINT_3.md).

## Reglas del equipo (D27-C05)

- **Ramas:** `main` (estable), `develop` (integración), `feature/<nombre-corto>` (una por historia).
- **Commits:** `[codigo-requisito] descripcion corta`, por ejemplo `[RF-01] agrega validacion de RUT`.
- **Nombres:** aplicaciones `nombreApp`; archivos y funciones en `snake_case`; clases en `PascalCase` (PEP 8).
- **Vistas** sin lógica de negocio: delegan en modelos o clases de dominio.
- **Funciones públicas** con un comentario del requisito (`# RF-01`).

## Trazabilidad con los documentos

| Documento | Relación con este repositorio |
|---|---|
| SRC02-C05 | Este código fuente |
| SRC03-C05 | Base y usuario de MySQL; las tablas las crean las migraciones |
| D45-C05 | Enlace a este repositorio |
| D21-C03 / D26-C03 | Clases y patrones de diseño implementados |
| D28-C06 / D29-C06 | Pruebas en `tests.py` de cada aplicación |
