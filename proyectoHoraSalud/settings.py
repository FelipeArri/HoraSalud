"""
Configuracion global de HoraSalud (Django 4.2).

Todas las credenciales se leen del archivo .env, que nunca se sube a Git
(RNF-SEC02). Ver .env.example para la lista de variables.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]

if not SECRET_KEY:
    raise RuntimeError('Falta DJANGO_SECRET_KEY en el archivo .env (ver .env.example).')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'autenticacionApp',   # RF-01, RF-03
    'agendaApp',          # RF-02, RF-04, RF-05
    'listaEsperaApp',     # RF-06
    'notificacionesApp',  # Factory Method + Strategy
    'pantallaApp',        # Pantalla de la sala de espera
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'proyectoHoraSalud.middleware.SinCacheParaSesionMiddleware',  # DEF-03
]

ROOT_URLCONF = 'proyectoHoraSalud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'autenticacionApp.sesion.contexto_sesion',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyectoHoraSalud.wsgi.application'

# Base de datos: MySQL/MariaDB de XAMPP (SRC03-C05).
# DB_ENGINE=sqlite solo se usa para correr pruebas rapidas sin XAMPP.
if os.getenv('DB_ENGINE') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_pruebas.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_ALL_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }

# Usuario propio con RUT y tipo de usuario (RF-01). Debe definirse antes del primer migrate.
AUTH_USER_MODEL = 'autenticacionApp.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # destino de collectstatic (D33-C07)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API REST: JWT y acceso solo con token por defecto (OWASP A01 y A07).
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Seguridad de cookies y cabeceras (RNF-SEC02, OWASP A05).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 30 * 60          # la sesion vence a los 30 min (RNF-SEC02)
SESSION_SAVE_EVERY_REQUEST = True     # ...contados desde el ultimo uso
LOGIN_URL = 'ingresar'

# Passkeys / WebAuthn (B-06). El navegador solo acepta passkeys en HTTPS o en
# http://localhost (no en 127.0.0.1).
WEBAUTHN_RP_NOMBRE = 'HoraSalud CESFAM'
WEBAUTHN_RP_IDS = ['localhost']
WEBAUTHN_ORIGENES = ['http://localhost:8000']

# B-16: dominio HTTPS del tunel de VS Code (Port Forwarding / Dev Tunnels) para
# usar la huella del telefono. Ej.: HORASALUD_DOMINIO_PUBLICO=abc123-8000.brs.devtunnels.ms
HORASALUD_DOMINIO_PUBLICO = os.getenv('HORASALUD_DOMINIO_PUBLICO', '').strip().lower()
if HORASALUD_DOMINIO_PUBLICO:
    WEBAUTHN_RP_IDS.append(HORASALUD_DOMINIO_PUBLICO)
    WEBAUTHN_ORIGENES.append(f'https://{HORASALUD_DOMINIO_PUBLICO}')
    ALLOWED_HOSTS.append(HORASALUD_DOMINIO_PUBLICO)
    # El tunel de VS Code reescribe la cabecera Origin a http://localhost:8000.
    # El token CSRF de cada formulario se sigue exigiendo igual (OWASP A01).
    CSRF_TRUSTED_ORIGINS = [f'https://{HORASALUD_DOMINIO_PUBLICO}', 'http://localhost:8000']
    # El tunel recibe HTTPS y lo entrega por HTTP al notebook. Estas cabeceras avisan
    # que la conexion original era segura y con que dominio llego el celular.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# B-07: clave para cifrar datos sensibles en la base (telefono, motivos).
# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Sin ella, solo en desarrollo, se deriva de SECRET_KEY. Si se pierde, esos datos no se pueden leer.
HORASALUD_CLAVE_CIFRADO = os.getenv('HORASALUD_CLAVE_CIFRADO', '')
if not HORASALUD_CLAVE_CIFRADO and not DEBUG:
    raise RuntimeError('Falta HORASALUD_CLAVE_CIFRADO en el archivo .env (ver .env.example).')

# Ingreso sin huella (modo demostracion). Solo con DEBUG y SOLO desde
# localhost: nunca desde el dominio publico del tunel (ver autenticacionApp.passkeys).
HORASALUD_INGRESO_DEMO = DEBUG and os.getenv('HORASALUD_INGRESO_DEMO', 'True') == 'True'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
if not DEBUG:
    # Fuera del modo desarrollo todo viaja por HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SSL_REDIRECT', 'True') == 'True'
    SECURE_HSTS_SECONDS = 3600
