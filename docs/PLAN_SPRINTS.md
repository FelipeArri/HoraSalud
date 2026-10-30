# Plan de sprints de construcción (propuesta)

Continúa el Sprint Backlog D42-C04 (Sprints 0 a 2 ejecutados en la Unidad 2).
Las **fechas quedan pendientes** hasta confirmar la fecha de presentación.
Cada tarea se convierte en una tarjeta de Trello y en una rama de Git.

| Sprint | Objetivo | Tareas principales | Requisitos | Evidencia de cierre |
|---|---|---|---|---|
| **3** | Base técnica y datos | Repositorio GitHub; proyecto Django con 5 aplicaciones; MySQL en XAMPP; `.env`; `/api/salud/`; modelos de D22 (usuario con RUT, paciente, tutor, agenda, bloque, hora, lista de espera); panel `/admin/`; datos ficticios (`cargar_datos_demo`); validación de RUT; 25 pruebas | RNF-SEC02, RN-01/RN-02 en base de datos | Capturas de inicio, `/api/salud/`, `/admin/` y phpMyAdmin; URL en D45 |
| **4** | Identidad y enrolamiento | Ingreso del paciente con RUT; inscripción simulada (Adapter); enrolamiento presencial con código de un solo uso; passkeys (WebAuthn); consentimiento; diseño visual según wireframes D23; PWA (manifiesto) | RF-01, RNF-SEC02 | Casos CP de RF-01 ejecutados |
| **5** | Reserva y tutor | Pantallas y API para reservar y cancelar; doble reserva → 409; vínculo de tutor autorizado por el paciente o por el SOME | RF-02, RF-03, RN-01 a RN-04 | Casos CP de RF-02 y RF-03 |
| **6** | SOME y No-Show | Panel SOME; nómina del día; No-Show tras 20 min; auditoría (RN-11); pantalla del CESFAM | RF-05, RF-04 | Casos CP de RF-05 y de seguridad OWASP |
| **7** | Cierre | Lista de espera (si alcanza); acceso desde el teléfono con HTTPS; demostración en AWS; corrección de defectos y regresión; documentos finales | RF-06, RNF-01 | Matriz de trazabilidad final, informe |

## Definición de terminado (por tarea)

- El código está en una rama `feature/...` con commits `[RF-XX]`.
- Tiene al menos una prueba automática o un caso CP ejecutado con captura.
- El otro integrante revisó el Pull Request.
- La tarjeta de Trello tiene enlazado el Pull Request.
