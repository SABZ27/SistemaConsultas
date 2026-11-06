# API REST

## 1. Introducción

El sistema expone dos API REST independientes:

- **FastAPI** (Python 3.13, `backend/`): 102 endpoints HTTP del dominio de
  negocio, agrupados en 17 routers.
- **Express** (Node 24, `infraestructura-service/`): 6 endpoints de servicios
  externos (festivos, correo y bitácora).

Ambas son **stateless** y usan JSON. La autenticación se realiza con JWT
firmado en **HS256**. La documentación interactiva la genera FastAPI
automáticamente en `/docs` y `/openapi.json`; este documento describe las
convenciones generales y la organización de rutas.

Nada de lo aquí descrito implica que el sistema esté desplegado o probado en
producción: el despliegue son **pasos pendientes**
(`docs/despliegue-render.md`).

---

## 2. Arquitectura y convenciones

- Cliente-servidor, sin sesiones en servidor: cada petición lleva su token.
- Recursos identificados por URI, en plural, con métodos HTTP estándar.
- Cuerpos y respuestas en JSON (`Content-Type: application/json`).
- Eliminación **lógica** mediante el campo `estado` (no `DELETE` físico).
- Los esquemas de entrada y salida son modelos **Pydantic v2** en FastAPI y
  **zod** en Express. No se usan DTO de Java ni Bean Validation.
- La autorización combina el **rol** y los **módulos** asignados a ese rol
  (`MATRIZ_MODULOS_X_ROL` en `app/db/seeds.py`); la matriz de acceso por rol
  está en `backend/tests/test_autorizacion_roles.py`.

---

## 3. Formato de solicitudes

```http
Content-Type: application/json
Authorization: Bearer <JWT>
```

`Authorization` es obligatorio salvo en las rutas públicas. El token es un JWT
HS256 con los claims `sub`, `uid`, `rol`, `modulos`, `iat` y `exp`; el backend
exige `exp/sub/uid/rol` y rechaza tokens con rol `SERVICIO` o `uid=0` en
endpoints de usuario.

**Límite de cuerpo:** **1 MiB** (`1024 * 1024` bytes). Un cuerpo mayor responde
`413`, también cuando llega *chunked* sin `Content-Length`. Express aplica el
mismo límite con `express.json({ limit: '1mb' })`.

---

## 4. Formato de respuestas y errores

Respuesta exitosa: JSON del recurso, o un mensaje de texto cuando la operación
no devuelve entidad (por ejemplo `"Contraseña actualizada correctamente."`).

Todos los errores tienen el mismo sobre, generado por
`app/exceptions/handlers.py` (`_cuerpo`) y, en Express, por
`src/utils/errores.js` (`cuerpoError`):

```json
{
  "timestamp": "2026-11-06T10:00:00.000000",
  "status": 400,
  "error": "Bad Request",
  "message": "Error de validación.",
  "errors": { "correo": "El correo es obligatorio" }
}
```

| Campo | Descripción |
|---|---|
| `timestamp` | Fecha y hora del error (ISO 8601) |
| `status` | Código HTTP |
| `error` | Nombre del código HTTP |
| `message` | Descripción general |
| `errors` | Errores por campo, o `null` |

Los errores no controlados responden `500` con un mensaje genérico: **el log
solo registra el tipo de excepción**, nunca correos, tokens ni contraseñas.

### Códigos HTTP utilizados

| Código | Uso |
|---|---|
| `200` / `201` / `204` | Operación correcta / creado / sin contenido |
| `400` | Validación (Pydantic/zod) o regla de negocio |
| `401` | Sin token, token inválido o expirado |
| `403` | Rol o módulo sin permiso; recurso ajeno |
| `404` | Recurso no encontrado |
| `413` | Cuerpo mayor de 1 MiB |
| `429` | Límite de solicitudes superado (incluye `Retry-After`) |
| `500` | Error interno no controlado |
| `502` | Proveedor externo de correo (Express) |
| `503` | No se pudo validar el festivo (fail-closed) o servicio externo no disponible |

`429` incluye la cabecera `Retry-After` con un entero de segundos (>= 1),
calculado por el limitador.

---

## 5. Autenticación y recuperación

Flujo:

1. `POST /auth/login` con `{"correo", "password"}` devuelve el JWT, el rol y
   los módulos del usuario.
2. El cliente envía `Authorization: Bearer <JWT>` en cada petición.
3. `GET /auth/me` devuelve el perfil del usuario autenticado.

Rutas públicas de FastAPI: `POST /auth/register`, `POST /auth/login`,
`POST /auth/forgot-password`, `POST /auth/reset-password`. En Express solo
`GET /health` es público.

### `POST /auth/cambiar-password` (requiere sesión)

Es **solo POST**; no existe un `GET` de ese recurso. Body real, según
`CambiarPasswordRequest` (`app/schemas/auth.py`):

```json
{
  "passwordActual": "...",
  "nuevaPassword": "..."
}
```

- `passwordActual`: obligatorio (longitud mínima 1).
- `nuevaPassword`: obligatoria; se valida con la política de contraseñas
  (mínimo 10 caracteres, máximo 72 bytes, mayúscula, minúscula, número y
  símbolo, sin datos personales ni contraseñas comunes).

El servicio (`AuthService.cambiar_password`) verifica la contraseña actual con
bcrypt, exige que la nueva sea **distinta** a la actual, aplica la política y
guarda el nuevo hash. Responde `200` con
`"Contraseña actualizada correctamente."`, o `400` con el motivo en `errors`.

### Recuperación de contraseña

`POST /auth/forgot-password` devuelve siempre la misma respuesta, exista o no
el correo, y **envía el correo en segundo plano** (`BackgroundTasks`). El token
se guarda **hasheado con SHA-256**, es de **un solo uso** y expira a los
**30 minutos**. `POST /auth/reset-password` recibe
`{"token", "nuevaPassword"}` y valida la política.

---

## 6. Límites de solicitudes (429)

Limitadores en memoria (`app/core/rate_limit.py`), con ventana deslizante y
tope global de **10.000 claves** por limitador (purga de vencidas y desalojo de
las más antiguas):

| Ámbito | Límite | Ventana | Bloqueo |
|---|---|---|---|
| Login por pareja correo+IP | 5 fallos | 15 min | 15 min |
| Login por correo | 15 fallos | 15 min | — |
| Login por IP | 100 fallos | 15 min | 15 min |
| Registro por IP / por correo | 10 / 5 solicitudes | 60 min | — |
| Recuperación por IP / por correo | 10 / 3 solicitudes | 15 min | — |
| Restablecimiento por IP / por token | 10 / 5 solicitudes | 15 min | — |

La clave de IP se obtiene de `X-Forwarded-For` con `TRUSTED_PROXY_HOPS` (por
defecto `0`); ver `docs/decisiones.md` para la medición. Sin medirlo, varios
clientes pueden quedar agrupados bajo la misma clave; el límite de 100 por IP
mitiga el efecto.

---

## 7. Organización de la API

**FastAPI (17 prefijos):**

```text
/auth                    /auth/me, /auth/register, /auth/login,
                         /auth/forgot-password, /auth/reset-password,
                         /auth/cambiar-password
/usuarios                /usuarios, /usuarios/docentes, /usuarios/{id},
                         /usuarios/{id}/activar
/roles                   /roles, /roles/{id}, /roles/{id}/modulos
/modulos-sistema
/modulos                 /modulos, /modulos/{id}, /modulos/{id}/docentes
/programas
/docentes-modulos
/disponibilidad-docente
/periodos-academicos
/tipos-documento
/sedes                   /sedes, /sedes/{id}/zonas,
                         /sedes/{id}/recursos-fisicos
/zonas                   /zonas, /zonas/{id}/recursos-fisicos
/recursos-fisicos
/solicitudes-consultas   listado, detalle, actualización, estado,
                         recurso-fisico, docente, calificación
/comentarios
/notificaciones          /notificaciones, /no-leidas/count,
                         /{id}/leer
/docentes                /docentes/{id}/calificaciones/promedio
```

**Express (6 rutas):**

```text
GET  /health                     público
GET  /festivos/validar           requiere token (fecha, pais)
GET  /festivos                   requiere token (anio)
POST /correos                    requiere token con rol SERVICIO
DELETE /festivos/:id             requiere token con rol ADMINISTRADOR
GET  /servicios-externos         requiere token
```

`POST /correos` usa un **token interno de servicio** (rol `SERVICIO`, 5
minutos, mismo `JWT_SECRET`); un token de usuario recibe `403`.

---

## 8. Métodos HTTP

| Método | Uso |
|---|---|
| `GET` | Consultar recursos |
| `POST` | Crear recursos / operaciones de autenticación |
| `PUT` | Reemplazar / actualizar |
| `PATCH` | Cambios parciales (estado, activación, lectura) |
| `DELETE` | Baja lógica (`estado = false`) |

---

## 9. Validación de datos

- FastAPI: **Pydantic v2** (`BaseModel`, `Field`, `model_validator`,
  `extra="ignore"`), con `email-validator` para correos. Los errores de
  validación se traducen al sobre de error con `400` y `errors` por campo.
- Express: **zod** en `src/validators/`, con el mismo formato de error.
- Reglas de negocio adicionales en los servicios (política de contraseñas,
  periodo académico vigente, festivos fail-closed con `503`, disponibilidad
  del docente, pertenencia del recurso).

---

## 10. Cabeceras de seguridad y CORS

- **CORS por lista** (`CORS_ORIGINS`), sin `*` y con credenciales.
- Cabeceras en todas las respuestas: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Permissions-Policy`, `Cross-Origin-Opener-Policy: same-origin`. Express
  añade Helmet y oculta `X-Powered-By`.
- **HSTS**: se emite `Strict-Transport-Security: max-age=31536000;
  includeSubDomains` cuando `request.url.scheme == "https"` **o** cuando llega
  `X-Forwarded-Proto: https`. Es la condición literal del código
  (`app/main.py`); no hay comprobación de confianza del proxy que envía esa
  cabecera, por lo que **no debe presentarse como protección contra
  falsificación de cabeceras**.
- Detalle completo en `docs/04-Seguridad.md`.

---

## 11. OpenAPI

FastAPI genera la documentación interactiva en **`/docs`** y el esquema en
**`/openapi.json`** al ejecutar el servicio. Esa es la fuente viva para el
detalle de cada operación, incluidos los modelos de petición y respuesta.

---

## 12. Estado y evolución

La API y sus 102 endpoints están cubiertos por la matriz de autorización de
`backend/tests/test_autorizacion_roles.py`, que falla si aparece una ruta no
declarada. Los cambios futuros de esquema se reflejan primero en los modelos
SQLAlchemy y en `init_db()`; los scripts de `docs/sql/` son una instantánea de
entrega, no una migración incremental.

No se documenta aquí ningún despliegue realizado: todos los pasos de puesta en
producción están pendientes.
