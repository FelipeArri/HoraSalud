# Base de datos descargable (solo datos ficticios)

Para instalar la base de HoraSalud en XAMPP sin correr los comandos de Django
uno por uno.

| Archivo | Qué hace | Dónde se ejecuta |
|---|---|---|
| `01_crear_base_y_usuario.sql` | Crea la base `horasalud_db` y el usuario `horasalud_app` | phpMyAdmin → pestaña **SQL** (cambia `tu_clave` antes) |
| `02_horasalud_demo.sql` | Crea todas las tablas y carga los datos ficticios | phpMyAdmin → pestaña **Importar** |

## Qué trae

- **18 usuarios ficticios:** 12 pacientes (2 con tutor), 2 tutores, 3 profesionales y 1 administrativo.
- **Agenda:** 3 sectores, 3 especialidades, 15 agendas con 180 bloques de 20 minutos.
- **Horas:** 15 horas reservadas y 3 pacientes en lista de espera.

## Privacidad (Ley 19.628 / 21.719, RNF-SEC02)

- Todos los RUT son ficticios (desde 30.000.001). No hay datos de personas reales.
- Ningún usuario de la demo puede iniciar sesión, porque sus claves están deshabilitadas.
- **No trae superusuario.** Cada integrante crea el suyo con
  `python manage.py createsuperuser`.
- Las claves reales (de la base y de Django) van solo en el `.env` de cada
  computador, que nunca se sube.

## Las fechas se desactualizan

Las agendas corresponden a los días hábiles siguientes a la fecha en que se
generó el archivo. Para tener agendas desde hoy:

```powershell
python manage.py cargar_datos_demo --limpiar
```

## Cómo se regenera este archivo

Cuando cambien los modelos (una nueva migración), hay que volver a generar
`02_horasalud_demo.sql`:

1. Crear una base vacía.
2. Ejecutar `migrate` y `cargar_datos_demo` sobre ella.
3. Exportarla con `mysqldump` sin superusuario.
4. Subir el archivo nuevo con un commit `[SPR-XX] actualiza base demo`.
