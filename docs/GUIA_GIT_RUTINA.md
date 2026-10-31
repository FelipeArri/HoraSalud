# Rutina de Git para cada bloque (HoraSalud)

Siempre el mismo orden. Los comandos van en la terminal de VS Code, con
`(venv)` activo y dentro de la carpeta `horasalud`.

```
main      ●────────────────────────●   versión estable (se entrega)
develop   ●──●──●──●──●──●──●──●──●    se junta el trabajo del equipo
             \     /  \     /
feature/x     ●──●     ●──●            un bloque de Trello = una rama
```

| Rama | Para qué | ¿Se trabaja directo en ella? |
|---|---|---|
| `main` | Versión estable para mostrar y entregar | **Nunca** |
| `develop` | Junta lo terminado de ambos integrantes | **Nunca**; solo recibe Pull Requests |
| `feature/...` | Un bloque de Trello | **Sí**, aquí se programa |

---

## A. Al EMPEZAR un bloque

```powershell
git checkout develop
```

```powershell
git pull
```

```powershell
git checkout -b feature/nombre-del-bloque
```

✅ **Comprueba:** `git branch --show-current` debe mostrar `feature/nombre-del-bloque`.

En Trello: mueve la tarjeta a **🔨 En curso**.

> Si hubo cambios en modelos o librerías (te lo avisa el compañero o el PR):
> `pip install -r requirements.txt` y `python manage.py migrate`.

## B. MIENTRAS trabajas (cuantas veces quieras)

```powershell
python manage.py test
```

✅ Debe terminar en `OK` antes de guardar.

```powershell
git add carpeta1 carpeta2 archivo.py
```

```powershell
git status
```

✅ **Revisa la lista verde** antes de seguir:

- **No** debe aparecer `.env` (claves) ni `venv/`.
- Solo deben estar los archivos del bloque.

```powershell
git commit -m "[RF-XX] qué hiciste, en pocas palabras"
```

## C. Al TERMINAR el bloque

```powershell
git push -u origin feature/nombre-del-bloque
```

En GitHub:

1. Presiona **Compare & pull request**.
2. ⚠️ **Revisa arriba:** `base: develop` ← `compare: feature/nombre-del-bloque`.
   Si dice `base: main`, **cámbialo a `develop`** (este fue el error del PR #1).
3. Pon un título y una descripción → **Create pull request**.
4. El otro integrante lo revisa → **Approve** → **Merge pull request** → **Confirm merge**.
5. **Delete branch** (opcional: borra la rama ya unida).

En Trello: mueve la tarjeta a **👀 En revisión** y luego a **✅ Terminado**.

Vuelve a tu computador:

```powershell
git checkout develop
```

```powershell
git pull
```

## D. Al CERRAR un sprint (solo entonces se toca `main`)

1. En GitHub: **New pull request** con `base: main` ← `compare: develop` → **Merge**.
2. En tu computador:

```powershell
git checkout main
```

```powershell
git pull
```

```powershell
git checkout develop
```

```powershell
git merge main
```

```powershell
git push
```

3. Etiqueta la versión (v0.5, v0.6…):

```powershell
git tag -a v0.5 main -m "qué incluye esta versión"
```

```powershell
git push origin v0.5
```

---

## Errores comunes y cómo salir

| Situación | Qué hacer |
|---|---|
| GitHub dice que las ramas son "identical" | Faltó `git commit` o `git push`. Revisa con `git status` y `git log --oneline -3` |
| Hice commit en `develop` por error (sin push) | `git branch feature/rescate` → `git reset --hard origin/develop` → `git checkout feature/rescate`. **Pide ayuda antes si no estás seguro** |
| `.env` aparece en `git status` | **No hagas commit.** `git restore --staged .env` y revisa que `.gitignore` tenga `.env` |
| PR creado con `base: main` | Edítalo en GitHub (botón **Edit** junto al título) y cambia la base a `develop` |
| `CRLF will be replaced by LF` | Es solo un aviso de Windows; puedes seguir |
| Conflicto al hacer `git pull` | No borres nada; avisa al compañero y revísenlo juntos |

## Formato de los commits

`[código] descripción corta en minúscula`

- `[RF-02] agrega cancelación con motivo`
- `[RN-04] valida plazo de 2 horas para cancelar`
- `[DEF-03] evita mostrar páginas privadas tras cerrar sesión`
- `[SPR-04] cierre de sprint`
