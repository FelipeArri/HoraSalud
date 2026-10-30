# Guía Sprint 3: repositorio, base de datos y proyecto funcionando

**Objetivo:** dejar HoraSalud corriendo en el notebook, conectado a MySQL de
XAMPP y subido a GitHub. Todo es gratuito.

**Resultado esperado:** <http://127.0.0.1:8000/> muestra la página de inicio y
<http://127.0.0.1:8000/api/salud/> responde `{"api": "ok", "baseDatos": "ok"}`.

Igual que en el instructivo de Back End, cada paso tiene el concepto, los
comandos para copiar y qué hace cada uno. Todos los comandos van en la
**terminal de VS Code (PowerShell)**. 👥 = lo hacen ambos integrantes.

Ubicación del proyecto:
`C:\Users\felip\Documents\inacap2.0\ingenieria en software\proyecto semestral\horasalud`

---

## Paso 1. Abrir el proyecto en VS Code 👥

```powershell
cd "C:\Users\felip\Documents\inacap2.0\ingenieria en software\proyecto semestral\horasalud"
```

```powershell
code .
```

**Qué hace:** entra a la carpeta del proyecto y la abre en VS Code. Desde
ahora usa la terminal de VS Code (menú Terminal → Nueva terminal).

## Paso 2. Crear y activar el entorno virtual 👥

El proyecto usa **Python 3.11** (Django 4.2 no funciona con 3.13).

```powershell
py -3.11 -m venv venv
```

```powershell
.\venv\Scripts\Activate.ps1
```

**Qué hace:** crea la carpeta `venv\` con un Python aislado y lo activa. Al
inicio de la línea debe aparecer `(venv)`. Si PowerShell bloquea el script,
usa el mismo comando del instructivo (sección 1.2):
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

## Paso 3. Instalar las librerías 👥

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements.txt
```

**Qué hace:** instala Django, Django REST Framework, JWT, el cliente de MySQL
y python-dotenv, con las mismas versiones para los dos integrantes.

## Paso 4. Crear la base de datos en XAMPP 👥

1. Abre **XAMPP Control Panel** y presiona **Start** en **Apache** y en **MySQL** (deben quedar en verde).
2. Abre <http://localhost/phpmyadmin>.
3. Pestaña **SQL**, pega la **PARTE 1** del script
   `CESFAM_PadreEstebanGumucio_PROY\C05_Codigo_y_Versionamiento (SRC)\SRC03-C05-Src_ScriptsBaseDatos.sql`
   (desde `CREATE DATABASE` hasta `FLUSH PRIVILEGES;`).
4. **Antes de ejecutar**, cambia `cambiar_esta_clave` por una clave tuya y anótala.
5. Presiona **Continuar**.

**Qué hace:** crea la base `horasalud_db` y el usuario `horasalud_app`, que
solo tiene permisos sobre esa base y sobre la base temporal de pruebas
(mínimo privilegio). **No** ejecutes la
PARTE 2: las tablas las crea Django en el paso 7.

> XAMPP trae **MariaDB**, la versión compatible de MySQL. Django la usa igual.

## Paso 5. Crear el archivo .env 👥

```powershell
copy .env.example .env
```

Genera una clave secreta para Django:

```powershell
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Abre `.env` en VS Code y completa:

- `DJANGO_SECRET_KEY` = la clave que apareció en la terminal.
- `DB_PASSWORD` = la clave que pusiste en el paso 4.

**Qué hace:** las credenciales quedan fuera del código y **no** se suben a
GitHub (`.env` está en `.gitignore`). Es lo que pide RNF-SEC02.

## Paso 6. Correr las pruebas 👥

```powershell
python manage.py test
```

**Qué hace:** ejecuta las 25 pruebas automáticas (estados de la hora, reserva,
doble reserva, JWT, cabeceras de seguridad, patrones). Debe terminar en `OK`.
Django crea una base temporal `test_horasalud_db` y la borra al final.

## Paso 7. Crear las tablas y el superusuario 👥

```powershell
python manage.py migrate
```

```powershell
python manage.py createsuperuser
```

```powershell
python manage.py cargar_datos_demo
```

**Qué hace:** `migrate` crea las tablas en `horasalud_db` a partir de los
modelos (revísalas en phpMyAdmin: `autenticacionapp_usuario`,
`agendaapp_hora`, etc.). `createsuperuser` crea tu cuenta para el panel
`/admin/`; pide nombre de usuario, correo y clave (el RUT puede quedar vacío).
`cargar_datos_demo` llena la base con datos **ficticios**: 3 sectores,
3 especialidades, 3 profesionales, 12 pacientes (2 con tutor), agendas de
los próximos 5 días hábiles con bloques de 20 minutos, 15 horas y 3
pacientes en lista de espera. Si lo ejecutas de nuevo no duplica nada; con
`--limpiar` borra los datos demo y los vuelve a cargar.

## Paso 8. Levantar el servidor 👥

```powershell
python manage.py runserver
```

Abre en el navegador y **saca una captura de cada una** (son la evidencia del sprint):

1. <http://127.0.0.1:8000/> → página de inicio de HoraSalud.
2. <http://127.0.0.1:8000/api/salud/> → `{"api": "ok", "baseDatos": "ok"}`.
3. <http://127.0.0.1:8000/admin/> → entra con tu superusuario. Abre **Horas**:
   prueba filtrar por estado, editar una hora y cambiarle el estado. Luego
   revisa en phpMyAdmin que el cambio quedó guardado en `agendaapp_hora`.

Para detener el servidor: `Ctrl + C`.

## Paso 9. Crear el repositorio en GitHub (Felipe)

1. Entra a <https://github.com> (crea una cuenta si no tienes; es gratis).
2. **+ → New repository**. Nombre: `HoraSalud`. Visibilidad: **Public** (no hay secretos ni datos reales; permite proteger ramas gratis).
   **No** marques README, .gitignore ni license.
3. Pulsa **Create repository** y copia la URL (`https://github.com/FelipeArri/HoraSalud.git`).
4. **Settings → Collaborators → Add people** → el usuario de GitHub de Cristian.

## Paso 10. Primer commit y subida (Felipe)

Solo la primera vez en el computador:

```powershell
git config --global user.name "Felipe Arriaza"
```

```powershell
git config --global user.email "tu_correo_de_github@ejemplo.com"
```

Luego, desde la carpeta `horasalud`:

```powershell
git init -b main
```

```powershell
git add .
```

```powershell
git status
```

**Revisa** que en la lista **no** aparezcan `.env` ni `venv/`. Si aparecen, detente y avísame.

```powershell
git commit -m "[SPR-03] estructura inicial Django, configuracion segura y pruebas base"
```

```powershell
git remote add origin https://github.com/FelipeArri/HoraSalud.git
```

```powershell
git push -u origin main
```

```powershell
git checkout -b develop
```

```powershell
git push -u origin develop
```

**Qué hace:** sube el proyecto a `main` y crea la rama `develop`, donde se
integra el trabajo de cada sprint (D27-C05).

## Paso 11. Cristian clona el repositorio (Cristian)

Después de aceptar la invitación de GitHub:

```powershell
git clone https://github.com/FelipeArri/HoraSalud.git
```

Luego repite los pasos 2 a 8 en su computador, con su propia clave en `.env`.

## Paso 12. Cierre del sprint

Envíame:

1. La URL del repositorio (la registro en D45-C05 y D01-C08).
2. Las tres capturas del paso 8.
3. Cualquier error, copiado tal cual.

---

### Cómo trabajaremos desde el Sprint 4

1. Cada tarjeta de Trello es una rama: `git checkout develop` y luego
   `git checkout -b feature/validar-rut`.
2. Commits con el código del requisito: `[RF-01] agrega validacion de digito verificador`.
3. Al terminar: `git push` y en GitHub se abre un **Pull Request** hacia `develop`.
   El otro integrante lo revisa y lo aprueba: esa es la evidencia de "Revisado".
4. Al cerrar el sprint, `develop` se une a `main`.

### Problemas frecuentes

| Mensaje | Causa | Solución |
|---|---|---|
| `Falta DJANGO_SECRET_KEY` | No existe `.env` o está vacío | Repite el paso 5 |
| `Can't connect to MySQL server` | MySQL detenido en XAMPP | Start en MySQL (paso 4) |
| `Access denied for user 'horasalud_app'` | La clave de `.env` no coincide | Revisa `DB_PASSWORD` |
| `No module named 'django'` | Entorno virtual sin activar | `.\venv\Scripts\Activate.ps1` |
