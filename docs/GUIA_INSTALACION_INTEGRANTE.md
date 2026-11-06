# Guía rápida: instalar HoraSalud en tu computador

Para que cualquier integrante (Cristian) descargue el proyecto desde GitHub,
lo haga funcionar en su notebook y trabaje con Git.

Cada computador tiene **su propia base de datos** en XAMPP, con datos
ficticios. Lo que se comparte es el **código**, a través de GitHub; los datos
no se comparten.

Todos los comandos van en la **terminal de VS Code** (Terminal → Nueva terminal).

---

## Antes de empezar (una sola vez)

Instala lo que falte (todo es gratis):

| Programa | Dónde | Comprobar en la terminal |
|---|---|---|
| Git | <https://git-scm.com> | `git --version` |
| Python **3.11** | <https://www.python.org/downloads/release/python-3119/> (marca "Add to PATH") | `py -3.11 --version` |
| VS Code | <https://code.visualstudio.com> | — |
| XAMPP | <https://www.apachefriends.org> | — |
| Cuenta GitHub | <https://github.com> | — |

Luego:

1. Acepta la invitación al repositorio que te llega al correo, o entra a
   <https://github.com/FelipeArri/HoraSalud/invitations>.
2. Configura tu nombre en Git (con tu correo de GitHub):

```powershell
git config --global user.name "Cristian Plaza"
```

```powershell
git config --global user.email "tu_correo_de_github"
```

---

## Parte 1. Descargar el proyecto

Elige una carpeta, por ejemplo Documentos:

```powershell
cd $HOME\Documents
```

```powershell
git clone https://github.com/FelipeArri/HoraSalud.git
```

```powershell
cd HoraSalud
```

```powershell
code .
```

**Qué hace:** descarga el proyecto a la carpeta `HoraSalud` y lo abre en VS Code.
Si pide iniciar sesión en GitHub, elige "Sign in with your browser".

## Parte 2. Preparar Python

```powershell
py -3.11 -m venv venv
```

```powershell
.\venv\Scripts\Activate.ps1
```

✅ La línea debe empezar con `(venv)`. Si sale error de "ejecución de scripts
deshabilitada", ejecuta una vez
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` y repite.

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements.txt
```

✅ Comprueba: `python -m django --version` debe responder `4.2.24`.

## Parte 3. Instalar la base de datos (carpeta `base_datos`)

1. Abre **XAMPP Control Panel** → **Start** en **Apache** y **MySQL**.
2. Entra a <http://localhost/phpmyadmin>.
3. **Crear la base y el usuario:** abre en VS Code
   `base_datos\01_crear_base_y_usuario.sql`, copia su contenido y pégalo en
   la pestaña **SQL** de phpMyAdmin. **Cambia `tu_clave`** por una clave tuya
   (anótala) y presiona **Continuar**. Las líneas verdes son lo importante;
   los avisos "#1046 Base de datos no seleccionada" se pueden ignorar.
4. **Cargar tablas y datos ficticios:** pestaña **Importar** → **Seleccionar
   archivo** → `base_datos\02_horasalud_demo.sql` → **Continuar** (abajo).

✅ En el panel izquierdo, `horasalud_db` ya tiene tablas
(`agendaapp_hora`, `autenticacionapp_usuario`, etc.) con datos.

> El script `01_crear_base_y_usuario.sql` crea **dos bases**: `horasalud_db`
> (la aplicación) y `fonasa_simulado` (FONASA simulado, un sistema externo).

## Parte 4. Crear el archivo .env (tus claves)

```powershell
copy .env.example .env
```

```powershell
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Genera también la clave para cifrar datos sensibles:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Abre `.env` y completa, con comillas simples y sin espacios junto al `=`:

```
DJANGO_SECRET_KEY='el texto largo que salió en la terminal'
DB_PASSWORD='la clave que pusiste en phpMyAdmin'
HORASALUD_CLAVE_CIFRADO='la clave que salió con el segundo comando'
```

⚠️ No pierdas `HORASALUD_CLAVE_CIFRADO`: sin ella no se pueden leer los teléfonos guardados.

Guarda con Ctrl + S. **El `.env` nunca se sube a GitHub** (ya está en `.gitignore`).

## Parte 5. Probar y crear tu administrador

Crea las tablas y las 25 personas ficticias del FONASA simulado:

```powershell
python manage.py migrate --database=fonasa
```


```powershell
python manage.py test
```

✅ Debe terminar en `OK`.

```powershell
python manage.py createsuperuser
```

**Qué hace:** crea **tu propia** cuenta para entrar a `/admin/`. Nadie te
tiene que pasar una clave: la eliges tú aquí.

Opcional, para tener agendas desde hoy (las del archivo pueden ser de días
pasados):

```powershell
python manage.py cargar_datos_demo --limpiar
```

## Parte 6. Abrir el sistema

```powershell
python manage.py runserver
```

- <http://127.0.0.1:8000/> → página de inicio.
- <http://127.0.0.1:8000/api/salud/> → `{"api": "ok", "baseDatos": "ok"}`.
- <http://127.0.0.1:8000/admin/> → entra con tu superusuario.

Para detener: `Ctrl + C`.

---

## Cada día que trabajes

```powershell
cd $HOME\Documents\HoraSalud
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
git checkout develop
```

```powershell
git pull
```

```powershell
python manage.py migrate
```

**Qué hace:** entra al proyecto, activa Python, se pone en la rama de trabajo
y baja lo último que subió el compañero (y sus cambios en tablas, si hay).

## Para empezar una tarea de Trello

```powershell
git checkout -b feature/nombre-de-la-tarea
```

Trabajas, y al terminar:

```powershell
git add .
```

```powershell
git status
```

Revisa que no aparezcan `.env` ni `venv/`.

```powershell
git commit -m "[RF-XX] qué hiciste"
```

```powershell
git push -u origin feature/nombre-de-la-tarea
```

En GitHub aparece el botón **Compare & pull request**: ábrelo hacia `develop`.
El otro integrante lo revisa y lo aprueba. Mueve la tarjeta de Trello a
"En revisión".

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `No module named 'django'` | Falta activar el entorno: `.\venv\Scripts\Activate.ps1` |
| `python --version` dice 3.13 | El entorno no está activo, o se creó sin `-3.11` |
| `Falta DJANGO_SECRET_KEY` | No existe `.env` o no se guardó (Parte 4) |
| `Can't connect to MySQL server` | MySQL apagado en XAMPP |
| `Access denied for user 'horasalud_app'` | La clave de `.env` no coincide con la de phpMyAdmin |
| `Repository not found` al clonar | Aún no aceptas la invitación de GitHub |
