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
