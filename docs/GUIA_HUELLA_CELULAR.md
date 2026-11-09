# Guía B-16: usar la huella del celular (HTTPS con el túnel de VS Code)

**Por qué:** el celular solo permite passkeys (huella o rostro) en páginas
**HTTPS**. VS Code trae incorporado **Port Forwarding** (Dev Tunnels, de
Microsoft), que crea un enlace seguro como
`https://abc123-8000.brs.devtunnels.ms` hacia el servidor del notebook.
**No hay que instalar nada.**

> Es un **entorno de prueba**: el notebook es el servidor y el celular es el
> cliente. El túnel se abre solo para probar o para la demostración y luego se cierra.
>
> Se descartaron ngrok (Windows Defender lo bloqueó por reputación) y
> Tailscale (su inicio de sesión no respondió). Ambos se desinstalaron.

---

## Abrir el túnel

1. **Terminal 1** (con `(venv)`, en la carpeta `horasalud`):

   ```powershell
   python manage.py runserver
   ```

2. En el panel inferior de VS Code, abre la pestaña **PUERTOS** (*PORTS*), al
   lado de **TERMINAL**. Si no aparece: `Ctrl + Shift + P` →
   `Puertos: Centrarse en la vista Puertos` (*Ports: Focus on Ports View*).
3. Presiona **Reenviar un puerto** (*Forward a Port*), escribe `8000` y presiona Enter.
4. La primera vez pide **iniciar sesión con GitHub**: acepta y autoriza en el navegador.
5. En la fila del puerto 8000: **clic derecho → Visibilidad del puerto →
   Público** (*Port Visibility → Public*).
6. Copia la **Dirección reenviada** (*Forwarded Address*), por ejemplo
   `https://abc123-8000.brs.devtunnels.ms`.

## Decirle a HoraSalud cuál es el dominio

En `.env` (sin `https://` y sin `/` al final):

```
HORASALUD_DOMINIO_PUBLICO=abc123-8000.brs.devtunnels.ms
```

Guarda y reinicia el servidor (`Ctrl + C` → `python manage.py runserver`).

## Usarlo en el celular

Abre la dirección reenviada en Chrome (Android) o Safari (iPhone). La primera
vez aparece un aviso de Microsoft ("You are about to connect to a developer
tunnel"): presiona **Continue**.

**Para cerrar:** en la pestaña PUERTOS, clic derecho en el puerto 8000 →
**Detener reenvío de puerto** (*Stop Forwarding Port*). Desde ese momento
nadie más puede entrar.

---

## Prueba completa (evidencia B-16)

1. **Notebook, como SOME** (`http://localhost:8000`): Sofía (`30.000.004-5`)
   en modo demostración o tu superusuario → **Activar huella** → RUT del
   paciente → confirma la cédula → **Generar código**.
2. **Celular**: `https://…/activar-huella/` → RUT + código →
   **Registrar mi huella** → pon tu huella.
3. **Celular**: cierra sesión → **Ingresar** → RUT → **Usar mi huella** → huella.
4. Saca capturas de los pasos 2 y 3 en el celular.

## App instalable y avisos en el celular (B-14 y B-23)

Los avisos push también exigen HTTPS, así que se prueban por el túnel.

1. Una sola vez en el notebook: `python manage.py generar_claves_push` (agrega
   las claves a `.env`) y reinicia el servidor.
2. **Celular** (Chrome en Android), con la sesión del paciente iniciada: en
   **Mi inicio** aparece el panel **"HoraSalud en tu teléfono"**.
   - **Instalar HoraSalud** → queda el ícono verde en la pantalla de inicio.
   - Abre HoraSalud **desde el ícono** → **Activar avisos** → **Permitir**.
   - **Probar aviso** → el teléfono debe sonar y vibrar. Repite con la app cerrada.
3. **Lista de espera:** inscribe al paciente del celular en una especialidad
   sin horas; desde otra cuenta cancela una hora de esa especialidad con más de
   48 h de anticipación → el celular recibe "Se liberó una hora para ti".
4. **Recordatorio:** con una hora para mañana, entre 08:00 y 20:00, el celular
   recibe "Recuerda: mañana tienes hora…" (como máximo un minuto después).
5. Capturas: ícono instalado, aviso en la pantalla bloqueada y pantalla de la oferta.

## Modo producción (para la demostración)

`runserver` es solo para programar. Para la demostración se usa el servidor
de producción (waitress), que además deja corriendo las tareas automáticas:

1. En `.env`: `DJANGO_DEBUG=False` y el `HORASALUD_DOMINIO_PUBLICO` del túnel.
2. **Terminal 1:** `python manage.py migrate` (solo si hay migraciones nuevas) y luego:

   ```powershell
   python servidor.py
   ```

3. Abre el túnel del puerto 8000 como arriba.

Diferencias con el modo desarrollo:
- Todo se usa por la **dirección HTTPS del túnel**, también en el notebook:
  `http://localhost:8000` redirige a HTTPS y no funciona.
- **No existe el botón "Entrar sin huella"**. El SOME entra por
  **Ingreso de personal** con RUT y clave (`reportes/cuentas_personal.xlsx`).
- Los estilos e imágenes se sirven comprimidos y con versión (whitenoise).
- Para volver a programar: `DJANGO_DEBUG=True` en `.env` y `python manage.py runserver`.

## Seguridad mientras el túnel está abierto

- El botón **"Entrar sin huella (modo demostración)" no existe** para nada que
  llegue por el túnel, aunque alguien intente falsificar la dirección.
- Una passkey solo funciona en el dominio donde se creó (protección contra
  phishing del estándar WebAuthn): la del notebook no sirve en el celular.
- La base solo tiene **datos ficticios**. Cierra el túnel al terminar.
- Si el dominio del túnel cambia, hay que actualizar `.env` y volver a
  registrar la huella del celular.

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `Bad Request (400)` en el celular | Falta el dominio en `.env` o no reiniciaste el servidor |
| `CSRF verification failed` | El dominio en `.env` no coincide exactamente con la dirección reenviada |
| Pide iniciar sesión de GitHub en el celular | Falta cambiar la visibilidad del puerto a **Público** |
| "El navegador bloqueó la huella" | Entraste por una dirección distinta a la del `.env` |
| El celular no ofrece huella | Activa el desbloqueo con huella en el celular y usa Chrome o Safari |
| No aparece "Instalar HoraSalud" | Ábrela por la dirección HTTPS en Chrome; si ya está instalada, ábrela desde el ícono |
| "Los avisos están bloqueados" | Ajustes de Chrome → Notificaciones → permitir para la dirección del túnel |
| "Probar aviso" dice que faltan claves | Ejecuta `python manage.py generar_claves_push` y reinicia |
| En modo producción la página se ve sin estilos | Reinicia con `python servidor.py` (prepara los estilos al iniciar) |
