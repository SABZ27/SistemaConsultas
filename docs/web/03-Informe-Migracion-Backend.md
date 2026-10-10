# Informe de migración: Backend Kotlin/Spring → Python/FastAPI

**Fecha:** 2026-10-07
**Alcance:** Migración completa del backend Kotlin (Spring Boot) a Python (FastAPI) dentro de `backend/`, replicando los contratos reales (rutas, códigos HTTP, mensajes, estructura de error y serialización) verificados contra el código fuente Kotlin.

---

## 1. Resumen

- Se reemplazó el backend Spring Boot (Gradle, `src/main/kotlin/...`) por una API FastAPI en `backend/`.
- El backend Kotlin fue eliminado del repositorio (paso aprobado por el equipo) tras completar la verificación.
- Los contratos de API se replican **exactos** a los del Kotlin: rutas, métodos, códigos de estado, payloads `camelCase` y mensajes de error.
- Postgres (Neon) como base de datos de producción; SQLite para la suite de tests.
- Resultado: **44/44 tests en verde** (SQLite) y **23/23 verificaciones de comportamiento OK contra la base real de Neon**.

---

## 2. Estructura del backend Python

```
backend/
├── app/
│   ├── main.py                  # Factory de la app, CORS, middleware de autenticación
│   ├── api/
│   │   ├── deps.py              # Dependencias get_current_user (obligatorio/opcional)
│   │   └── routes/              # auth, usuarios, programas, modulos, sedes,
│   │                            # bloques, recursos, solicitudes_consultas,
│   │                            # comentarios, notificaciones
│   ├── core/                    # config (pydantic-settings) y security (JWT)
│   ├── db/                      # engine/session y Base declarativa
│   ├── exceptions/              # errores de dominio y handlers de formato
│   ├── mappers/                 # ORM → schemas de respuesta
│   ├── models/                  # modelos SQLAlchemy + enums
│   ├── repositories/            # acceso a datos
│   ├── schemas/                 # contratos Pydantic (requests/responses)
│   ├── services/                # lógica de negocio (réplica de los *Service* Kotlin)
│   └── utils/                   # numeración SC-{AÑO}-000001, contexto de usuario
└── tests/                       # conftest + helpers + 4 módulos de prueba
```

---

## 3. Inventario de endpoints migrados

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| POST | `/auth/register` | Público | 201, devuelve `"Usuario registrado correctamente."`; permite registro por rol (incl. ADMINISTRADOR) como en Kotlin |
| POST | `/auth/login` | Público | `token, id_usuario, correo, nombre, rol, tipo="Bearer"` |
| POST | `/auth/forgot-password` | Público | 200 `"Se ha generado un token de recuperación."` |
| POST | `/auth/reset-password` | Público | 200 `"Contraseña actualizada correctamente."` |
| GET / POST | `/programas` | GET público; POST admin | `Según SecurityConfig.kt`, `GET /programas` es `permitAll` |
| GET / PUT / DELETE | `/programas/{id}` | Autenticado | DELETE = 204 lógico |
| GET/POST, GET/PUT/DELETE | `/modulos`, `/sedes`, `/bloques`, `/recursos-fisicos` | Autenticado | 201 en POST; 204 lógico en DELETE |
| GET | `/usuarios`, `/usuarios/{id}` | Autenticado | |
| PUT / DELETE | `/usuarios/{id}` | Autenticado | 204 lógico |
| GET / POST | `/solicitudes-consultas` | Auth opcional/estudiante | POST valida rol ESTUDIANTE |
| GET / PUT | `/solicitudes-consultas/{id}` | Autenticado | |
| PATCH | `/solicitudes-consultas/{id}/estado` | Autenticado | transición + motivo obligatorio en RECHAZADA/CANCELADA |
| PATCH | `/solicitudes-consultas/{id}/recurso-fisico` | Autenticado | |
| PATCH | `/solicitudes-consultas/{id}/docente` | Autenticado | |
| POST / GET | `/comentarios`, `/comentarios/solicitud/{id}`, `/comentarios/{id}` | Autenticado | |
| PUT | `/comentarios/{id}` | Autenticado | solo autor |
| GET | `/notificaciones`, `/notificaciones/no-leidas/count` | Autenticado | |
| PATCH | `/notificaciones/{id}/leer` | Autenticado | solo destinatario |

### Formato de error unificado
`{"timestamp": ..., "status", "error", "message", "errors"}` (para 422, `errors` agrupa las validaciones de Pydantic, p. ej. `El asunto no puede estar vacío`).

---

## 4. Contratos y mensajes clave replicados

- Login: campos camelCase basados en el `LoginResponse.kt` real (incluye `tipo: "Bearer"`).
- Registro: correo duplicado `"El correo ya está registrado"`, identificación `"La identificación ya está registrada."`.
- Programa inexistente al registrar: `"Programa académico no encontrado"`.
- Solicitudes: `"El usuario indicado no tiene el rol ESTUDIANTE."`, fecha pasada `"La fecha de la consulta no puede ser anterior a la fecha actual."`, `"Debe indicar un motivo para RECHAZADA."`, `"La solicitud ya se encuentra en estado PENDIENTE."`, `"Debe indicar un motivo cuando se modifica la fecha o la hora de la consulta."`.
- Comentarios: `"No puede comentar esta consulta."`, `"Solo puedes editar tus propios comentarios."`.
- Notificaciones: `"Esta notificación no le pertenece."`
- 404 estándar con punto final: `"Programa académico no encontrado."`, `"Módulo no encontrado."`, `"Recurso físico no encontrado."`, `"Bloque no encontrado."`, `"Solicitud no encontrada."`, `"Docente no encontrado."`.
- Numeración de consultas: `SC-{AÑO}-000001` incremental.

---

## 5. Decisiones técnicas relevantes

1. **Contexto de usuario en endpoints síncronos.** Los services replican el patrón `obtenerUsuarioAuth()` del Kotlin leyendo un `ContextVar` (`app/utils/seguridad.py`). Como FastAPI corre los endpoints síncronos en un threadpool, la dependencia `get_current_user` (que vive en otro hilo) no propagaba el correo. Se resolvió con un **middleware ASGI** (`app/main.py`) que decodifica el Bearer token y establece el contexto antes del dispatch. *Sin este fix, todo endpoint cuyo service lee el usuario autenticado respondía 401.*
2. **Borrado lógico.** DELETE devuelve 204 y marca `activo = false`; las listas exponen solo registros activos, igual que el Kotlin.
3. **Enums string.** Los enums heredan de `str` (p. ej. `EstadoSolicitud.PENDIENTE`); los mensajes de error usan `.value` para no exponer `EstadoSolicitud.` como prefijo.
4. **Correos a consola.** `EmailService` imprime el correo en consola (mismo comportamiento del backend Kotlin); no hay SMTP configurado.
5. **Validación con `string_too_short` y `min_length=1`** produce `"El asunto no puede estar vacío"` (se corrigió el handler de validación).
6. **Registrar usuarios por rol** (ADMINISTRADOR/DOCENTE/ESTUDIANTE) vía `/auth/register`, tal como lo permitía el Kotlin.
7. **`GET /programas` público** (sin token), según `SecurityConfig.kt`; el resto exige token.
8. **`body` de módulos** no recibe `programaId` (coincide con el DTO Kotlin `RegistroModuloRequest`).

---

## 6. Verificación realizada

| Nivel | Resultado |
|---|---|
| Compilación | `python -m compileall -q app` OK |
| Suite de tests (SQLite) | **44 passed** en `pytest -q` (auth, CRUD, solicitudes, errores) |
| Smoke test uvicorn | Boot OK y `GET /docs` → HTTP 200 |
| Validación contra Neon | **23/23 comportamientos OK**: conexión + esquema, registro/login por rol, CRUD de catálogo, flujo completo de solicitud (crear → ver → EN_PROCESO → asignar recurso → comentario → notificación), rechazo con/sin motivo |

### Datos de prueba generados en Neon durante la validación
Durante la verificación se crearon registros con sufijo `verif`/correos `*_<timestamp>@test.com` (2 programas, 4 usuarios, 2 solicitudes, catálogo asociado, 1 comentario). Pueden depurarse manualmente si no se desea conservarlos.

---

## 7. Cómo ejecutar

```bash
# 1. Dependencias
cd backend
pip install -r requirements.txt        # o activar el venv existente

# 2. Configuración (Neon)
# backend/.env ya incluye DB_URL (Neon) + JWT_SECRET.
# Sin .env, se intenta postgres en localhost (Default de app/core/config.py).

# 3. Tests (SQLite, sin necesidad de Neon)
python -m pytest -q

# 4. Servidor
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 8. Pendientes / notas

- `JWT_SECRET` fue generado aleatoriamente en `backend/.env`; rotar si el repositorio llega a compartirse.
- Warning único en tests: `PendingDeprecationWarning` de `starlette/formparsers.py` (migración a `python_multipart`) — inofensivo.
- `docs/web/01-Plan-Migracion.md` y `docs/web/02-Auditoria-Cliente-Web-Backend.md` documentan el plan previo; este informe cierra el ciclo de migración.
- El frontend web (`Frontend/`) y la app móvil (`iubconsultas/`) no fueron modificados y siguen apuntando a la misma API.