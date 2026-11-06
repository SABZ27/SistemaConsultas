# Seguridad del Sistema

Este documento describe la seguridad **realmente implementada** en el
monorepo: FastAPI (Python 3.13) para el dominio y Express (Node 24) para los
servicios externos. No hay Spring Security, ni filtros de servlet, ni DTO de
Java. Nada de lo descrito implica que el sistema esté desplegado o probado en
producción: el despliegue son **pasos pendientes**.

---

## 1. Modelo general

- Arquitectura **stateless**: no hay sesiones en servidor; cada petición lleva
  su JWT.
- Dos servicios con el mismo `JWT_SECRET` (mínimo 32 caracteres, distinto del
  valor de ejemplo), para que el backend pueda firmar el token interno de
  servicio que consume Express.
- Autorización por **rol** (`ADMINISTRADOR`, `DOCENTE`, `ESTUDIANTE`) y por
  **módulos** asignados al rol (`MATRIZ_MODULOS_X_ROL` en `app/db/seeds.py`).
- Eliminación lógica con `estado`; errores centralizados con un mismo sobre
  JSON (`timestamp`, `status`, `error`, `message`, `errors`).

---

## 2. JWT (HS256)

`app/core/security.py`:

- `create_access_token` firma en **HS256** con payload `sub`, `uid`, `rol`,
  `modulos`, `iat` y `exp`. La expiración usa `JWT_EXPIRATION_MINUTES`, cuyo
  valor por defecto es **30** (`app/core/config.py:28`).
- `decode_token` exige `exp`, `sub`, `uid` y `rol` (`options.require`), y
  **rechaza** tokens con `rol == "SERVICIO"` o `uid == 0`, para que un token de
  servicio no sirva en endpoints de usuario.
- `get_current_user` (`app/api/deps.py`) busca al usuario activo por el correo
  del token; si no existe responde `401`.

`infraestructura-service/src/utils/jwt.js` valida HS256 y exige `exp`.

### Arranque

- `JWT_SECRET`: <32 caracteres o igual al placeholder → `RuntimeError`
  (`validar_jwt_secret`, `app/core/config.py:67-74`) / `Error`
  (`validarConfiguracion`, `src/config/env.js:62-79`). **Impide el arranque** en
  ambos servicios.
- `CORS_ORIGINS`: vacía o con `*` → `RuntimeError` / `Error`. **Impide el
  arranque**. Default `http://localhost:5173,http://localhost:3000`.
- `ADMIN_PASSWORD`: si falta alguna de `ADMIN_CORREO`, `ADMIN_PASSWORD`,
  `ADMIN_IDENTIFICACION`, **no se crea el administrador** y se registra un
  aviso (el arranque continúa). Si está presente y es débil sin administrador
  existente, `verificar_password_admin` lanza `AdminPasswordError` y **sí
  impide el arranque**.

Solo se documentan nombres de variables; **no hay secretos en el repositorio**.

---

## 3. Roles, módulos y diseño intencional

- `requiere_modulo(nombre)` (`app/api/deps.py`) comprueba
  `modulos_x_rol` activo y responde `403` si el rol no lo tiene.
- Los `GET` de catálogos (módulos, programas, periodos, tipos de documento,
  sedes, zonas, recursos físicos, disponibilidad, resumen de docentes) usan
  solo `get_current_user`: **cualquier usuario autenticado puede leerlos**.
  Las escrituras y activaciones exigen el módulo correspondiente.
- **Registro público**: `POST /auth/register` permite `ESTUDIANTE` y `DOCENTE`;
  `ADMINISTRADOR` se rechaza con `403` (`AuthService.registro`). `estado` y
  cualquier campo extra se ignoran (`extra="ignore"`) y el usuario queda
  activo. Una cuenta `DOCENTE` auto-registrada **no recibe consultas por sí
  sola**: necesita que un administrador la asigne al módulo
  (`docentes-modulos`) y que tenga disponibilidad. La limitación es de
  gobierno de cuentas y de enumeración de nombres; está documentada en
  `docs/cobertura-seguridad.md`.
- **Recursos ajenos** (consultas, comentarios, notificaciones) se comprueban en
  la capa de servicio con datos reales; la matriz de autorización está en
  `backend/tests/test_autorizacion_roles.py` y falla si aparece un endpoint no
  declarado.

---

## 4. Política de contraseñas

`app/core/password_policy.py`:

| Regla | Valor |
|---|---|
| Longitud mínima | **10 caracteres** (`:5`) |
| Longitud máxima | **72 bytes** UTF-8 (`:6`) |
| Término mínimo para comparar datos personales | **4** (`:7`) |
| Composición | al menos una mayúscula, una minúscula, un número y un símbolo; sin espacios |
| Otras | rechaza contraseñas comunes y que contengan correo, nombre, apellido o identificación |

Los mensajes están en `:9-20`, por ejemplo «La contraseña debe tener al menos
10 caracteres». `validar_password_admin` (`:96-107`) aplica la misma política
al administrador inicial. El hash se hace con **bcrypt**
(`hash_password` / `verify_password`, `app/core/security.py:15-23`).

Se valida en el registro, en `POST /auth/reset-password`, en
`POST /auth/cambiar-password` y al crear usuarios como administrador.

### `POST /auth/cambiar-password` (solo POST)

Requiere sesión. Body según `CambiarPasswordRequest`
(`app/schemas/auth.py:64-75`): `passwordActual` (obligatorio) y
`nuevaPassword`. El servicio (`AuthService.cambiar_password`,
`app/services/auth.py:190-208`) verifica la actual con bcrypt, exige que la
nueva sea **distinta**, aplica la política y guarda el hash. Responde `200` con
`"Contraseña actualizada correctamente."` o `400` con el motivo.

---

## 5. Recuperación de contraseña

`app/services/auth.py:124-188` y `app/api/routes/auth.py`:

- `POST /auth/forgot-password` da **la misma respuesta** exista o no el correo
  (no revela si la cuenta existe) y devuelve `200`.
- El correo se envía **en segundo plano** con `BackgroundTasks`, después del
  commit.
- El token se genera con `secrets.token_urlsafe(32)` y se guarda **hasheado con
  SHA-256** (`hash_token`, 64 caracteres hexadecimales); el plano solo viaja
  en el correo.
- Es **de un solo uso** (`utilizado`) y expira a los **30 minutos**
  (`fecha_expiracion`, `:142`).
- `POST /auth/reset-password` valida el token, que no esté usado, que no haya
  expirado y la política de la nueva contraseña.

---

## 6. Límites de solicitudes (429) y bloqueo

`app/core/rate_limit.py` (limitadores en memoria, por proceso):

| Ámbito | Límite | Ventana | Bloqueo |
|---|---|---|---|
| Login pareja correo+IP | **5** fallos (`:29`) | 15 min (`:30`) | 15 min (`:31`) |
| Login por correo | **15** fallos (`:34`) | 15 min (`:35`) | — |
| Login por IP | **100** fallos (`:40`) | 15 min (`:41`) | 15 min (`:42`) |
| Registro IP / correo | **10** / **5** (`:45-47`) | 60 min | — |
| Recuperación IP / correo | **10** / **3** (`:51-53`) | 15 min | — |
| Restablecimiento IP / token | **10** / **5** (`:57-59`) | 15 min | — |

- **Tope global: 10.000 claves** por limitador (`:26`). Al llenarse se purgan
  las vencidas y se desalojan las más antiguas (`_asegurar_capacidad`, `:200`).
- Mensajes: «Demasiadas solicitudes. Intenta de nuevo más tarde.» y
  «Demasiados intentos fallidos. Intenta de nuevo en 15 minutos.»
  (`:62-67`).
- El manejador `too_many_requests_handler`
  (`app/exceptions/handlers.py:138-151`) responde **`429`** con el sobre de
  error y la cabecera **`Retry-After`** (entero >= 1, `_segundos` en
  `rate_limit.py:219-220`).
- Un login correcto limpia solo la pareja correo+IP; los contadores por correo
  y por IP se conservan.

### IP del cliente y `TRUSTED_PROXY_HOPS`

`obtener_ip` (`app/core/rate_limit.py`) toma `X-Forwarded-For` en la posición
`-(TRUSTED_PROXY_HOPS + 1)` desde la derecha. Si **cualquier** entrada está
vacía, malformada o no es una IP válida, o si hay menos de `hops + 1`
entradas, se usa `request.client.host`.

- **`TRUSTED_PROXY_HOPS` vale `0` por defecto** (`app/core/config.py:35`,
  `Field(default=0, ge=0)`).
- **Sin medirlo**, si el valor no coincide con los proxies reales se toma la
  última entrada (la del edge), compartida por muchos clientes: **los usuarios
  quedan agrupados bajo una sola clave** y los límites por IP se vuelven
  globales, con riesgo de `429` masivo. El límite alto de **100 fallos por IP**
  (`:40`) **mitiga** ese impacto, pero no lo elimina; los límites por pareja
  (5) y por correo (15) siguen activos.
- La resolución por saltos **no valida la confianza de los proxies**: asume que
  el servicio solo recibe tráfico a través de los proxies de Render. El
  procedimiento de medición (N-1 con `DIAGNOSTICO_IP`) está en
  `docs/decisiones.md` y `docs/despliegue-render.md` y es un **paso
  pendiente**.
- `DIAGNOSTICO_IP` (`false` por defecto, `config.py:39`) registra **solo** el
  número de entradas de `X-Forwarded-For` y si existe `True-Client-IP`
  (conteos y booleanos), **nunca direcciones IP**.

---

## 7. CORS, cabeceras, HSTS y límite de cuerpo

`app/main.py:65-107` y `infraestructura-service/src/app.js`:

- **CORS por lista** (`CORS_ORIGINS`), `allow_credentials=True`, sin `*`;
  métodos `GET/POST/PUT/PATCH/DELETE/OPTIONS` y cabeceras
  `Authorization`, `Content-Type`.
- Cabeceras en todas las respuestas (`main.py:92-98`):
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`,
  `Permissions-Policy: geolocation=(), camera=(), microphone=()`,
  `Cross-Origin-Opener-Policy: same-origin`. Express usa **Helmet**
  (`frameguard: deny`) y deshabilita `X-Powered-By`.
- **HSTS** (`main.py:100-106`): se emite
  `Strict-Transport-Security: max-age=31536000; includeSubDomains` si
  `request.url.scheme == "https"` **o** si `X-Forwarded-Proto` (primer valor,
  en minúsculas) es `https`. Es la condición literal del código: **no hay gate
  de confianza** sobre quién envía esa cabecera, por lo que **no debe
  presentarse como protección contra falsificación de cabeceras**.
- **Límite de cuerpo 1 MiB** (`MAX_CUERPO_BYTES = 1024 * 1024`,
  `app/core/limite_cuerpo.py:9`): responde **`413`** con «El cuerpo de la
  solicitud es demasiado grande.» (`:10`), también con cuerpo *chunked* sin
  `Content-Length`. Express aplica el mismo límite.

---

## 8. Token interno rol `SERVICIO`

`app/core/security.py:69-84` y `infraestructura-service/src/routes/correoRoutes.js`:

- `crear_token_interno(minutos=5)` firma un JWT con `rol = "SERVICIO"`,
  `uid = 0` y `sub` de servicio, con el mismo `JWT_SECRET`.
- Solo **`POST /correos`** lo acepta (`requiereRol('SERVICIO')`). Un token de
  usuario autenticado recibe **`403`**.
- El token de usuario **no se reenvía** para el envío de correos; el correo se
  programa con `BackgroundTasks` y se envía tras el commit.
- En Express, `DELETE /festivos/:id` exige además `ADMINISTRADOR`; el resto de
  rutas exige `autenticar` salvo `GET /health`.

---

## 9. Festivos fail-closed

Desde el Bloque A, si el servicio externo no responde (red, timeout, 5xx o
respuesta inválida), la creación/reprogramación de una solicitud se rechaza con
**`503`** (`ServiceUnavailableException`, `handlers.py:131-135`). El cliente
usa un timeout propio de **45 s** y un reintento solo para errores de conexión
o 5xx. Los festivos ya guardados en caché se resuelven localmente. Detalle en
`docs/decisiones.md`.

---

## 10. Datos personales (Bloque G)

Sin eliminar campos del contrato (pasan a `str | None`):

- En `SolicitudConsultaResponse`, cada participante ve **solo su propia**
  identificación; la de la otra parte sale `null`; `ADMINISTRADOR` ve ambas.
- En `UsuarioResponse`, `identificacion` y `correo` solo los ve el propio
  usuario o el administrador; los demás roles reciben `null`.
- `MeResponse` y `LoginResponse` son del propio usuario y no se enmascaran.
- `DocenteResumen` / `DocenteResumenModulo`, comentarios y notificaciones no
  exponen identificación ni correo.

Detalle y limitaciones en `docs/cobertura-seguridad.md`.

---

## 11. Auditoría, cobertura y código documentado

- Auditoría de dependencias: `docs/auditoria-dependencias.md` (`pip-audit` sin
  hallazgos; `body-parser` 1.20.9 corregido en el Bloque G; `zod` diferido por
  ser un cambio mayor).
- Cobertura y limitaciones: `docs/cobertura-seguridad.md`.
- `get_current_user_optional` (`app/api/deps.py:49`) es **código muerto
  documentado y conservado**: no se elimina.
- Formato de errores y códigos: `docs/05-API.md`.
- Variables de entorno y arranque: `README.md` y `docs/despliegue-render.md`.

---

## 12. Alcance de este documento

Describe el código del repositorio. **No se ha ejecutado ninguna validación en
producción**, no se ha conectado a Neon ni a Aiven, y todos los pasos de
despliegue (incluidos el respaldo, la migración 005, la medición de
`TRUSTED_PROXY_HOPS` y el borrado manual de las 3 tablas viejas de Aiven) son
**pasos pendientes** recogidos en `docs/despliegue-render.md`. No se incluyen
secretos, contraseñas, correos personales ni nombres de usuario en este
documento.
