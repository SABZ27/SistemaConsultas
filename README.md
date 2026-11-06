# Sistema de Gestión de Consultas Académicas

Sistema para gestionar consultas académicas entre estudiantes, docentes y
administradores, con autenticación JWT basada en roles y módulos del sistema.

El monorepo tiene dos servicios **previstos** para desplegarse por separado en
**Render** (despliegue pendiente; no realizado ni probado en producción):

| Servicio | Stack | Base de datos |
|---|---|---|
| `backend/` | FastAPI + SQLAlchemy + Uvicorn (Python 3.13) | PostgreSQL (Neon) |
| `infraestructura-service/` | Express + Node 24 | MySQL (Aiven) |

## Arquitectura

- **PostgreSQL (Neon)**: contiene **19 tablas** del dominio de negocio, incluyendo `sedes`, `zonas` y `recursos_fisicos` con claves foráneas hacia `solicitudes_consultas` (`recurso_fisico_id`).
- **MySQL (Aiven)**: contiene las **4 tablas** de servicios externos (`servicios_externos`, `consultas_servicio_externo`, `festivos`, `correos_enviados`) con las relaciones definidas entre ellas.
- **FastAPI (backend)**: expone endpoints del dominio, incluyendo `/sedes`, `/zonas`, `/recursos-fisicos`. Valida fechas festivas al crear y reprogramar solicitudes, llamando al microservicio de servicios externos.
- **Express (infraestructura-service)**: expone servicios externos en `/festivos`, `/correos`, `/servicios-externos`. `POST /correos` solo acepta tokens con rol `SERVICIO`. Usa **Nager.Date** para festivos y **Brevo** para envío de correos transaccionales.
- **Scripts SQL de entrega**: [`docs/sql/LEEME.md`](docs/sql/LEEME.md) (esquema y semillas de ambos motores).

## Roles

- **ESTUDIANTE**: crea y da seguimiento a sus consultas, comenta y califica.
- **DOCENTE**: atiende consultas, gestiona su disponibilidad y asigna recursos.
- **ADMINISTRADOR**: administra usuarios, roles/módulos, catálogos y solicitudes.

El acceso a cada funcionalidad se controla por el rol y por los módulos del
sistema asignados a ese rol (claim `modulos` del JWT). La matriz de
autorización por rol está en `backend/tests/test_autorizacion_roles.py`.

## Seguridad

- **JWT HS256**: payload con `sub`, `uid`, `rol`, `modulos`, `iat` y `exp`;
  `decode_token` exige `exp/sub/uid/rol` y rechaza tokens con rol `SERVICIO` o
  `uid=0` en endpoints de usuario. `JWT_EXPIRATION_MINUTES=30`.
- **Política de contraseñas**: mínimo **10 caracteres**, máximo **72 bytes**,
  sin espacios, con mayúscula, minúscula, número y símbolo; rechaza contraseñas
  comunes y datos personales (correo, nombre, apellido, identificación). Se
  almacenan con **bcrypt**. El administrador inicial se valida con la misma
  política (`validar_password_admin`).
- **`POST /auth/cambiar-password`** (requiere sesión): body
  `{"passwordActual": "...", "nuevaPassword": "..."}`. Verifica la contraseña
  actual, exige que la nueva sea distinta y aplica la política; responde `200`
  o `400`. Es **solo POST** (no hay `GET` de ese recurso).
- **Recuperación**: el token se guarda **hasheado con SHA-256**, es de un solo
  uso y expira a los **30 minutos**. `POST /auth/forgot-password` da la misma
  respuesta exista o no el correo y envía el correo en segundo plano.
- **Límites 429 y bloqueo** (ventanas de **15 min** para login): **5** fallos
  por pareja correo+IP, **15** por correo y **100** por IP; el bloqueo dura
  **15 min** y la respuesta incluye `Retry-After`. Hay además límites de
  registro (10 por IP / 5 por correo por hora), recuperación y restablecimiento.
  El tope global es **10.000 claves** por limitador, con purga de vencidas.
- **IP del cliente**: `obtener_ip` toma `X-Forwarded-For` en la posición
  `-(TRUSTED_PROXY_HOPS + 1)` desde la derecha; cualquier entrada vacía,
  malformada o no IP válida hace caer a `request.client.host`.
  `TRUSTED_PROXY_HOPS=0` por defecto. Ver «Medición» más abajo.
- **CORS por lista**: sin `*` y con credenciales; **cabeceras** de seguridad
  (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, `Cross-Origin-Opener-Policy`) y **HSTS** cuando el
  esquema es HTTPS o llega `X-Forwarded-Proto: https` (ver
  `docs/04-Seguridad.md`).
- **Límite de cuerpo 1 MiB**: responde `413` también con cuerpo *chunked* sin
  `Content-Length`. Express aplica Helmet y el mismo límite.
- **Validación de festivos fail-closed**: si el servicio externo no responde se
  rechaza con **503** (desde el Bloque A). Los festivos ya en caché se
  resuelven localmente.
- **Token interno rol `SERVICIO`**: 5 minutos, mismo `JWT_SECRET`; solo
  `POST /correos` lo acepta, los tokens de usuario reciben `403`.
- **Datos personales (Bloque G)**: `identificacion`/`correo` y las
  identificaciones de la otra parte en una solicitud se devuelven como `null`
  según el rol, sin eliminar campos del contrato.

Detalle completo en [`docs/04-Seguridad.md`](docs/04-Seguridad.md),
[`docs/cobertura-seguridad.md`](docs/cobertura-seguridad.md) y
[`docs/auditoria-dependencias.md`](docs/auditoria-dependencias.md).

## Cómo ejecutar en local

Backend (FastAPI):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Servicio de infraestructura (Express):

```bash
cd infraestructura-service
npm install
npm start            # http://localhost:3001
```

## Variables de entorno

Cada servicio incluye una plantilla `.env.example` con los **nombres** de las
variables y valores de ejemplo (nunca reales). Solo se documentan nombres,
defaults y efectos en el arranque; **no hay secretos en este repositorio**.

| Variable | Servicio | Valor por defecto | ¿Impide el arranque? |
|---|---|---|---|
| `JWT_SECRET` | Ambos | placeholder de ejemplo | **Sí**: <32 caracteres o el placeholder (`validar_jwt_secret` / `validarConfiguracion`). Debe ser idéntico en ambos servicios |
| `CORS_ORIGINS` | Ambos | `http://localhost:5173,http://localhost:3000` | **Sí**: vacía o con `*` |
| `ADMIN_PASSWORD` | Backend | vacío | Si falta alguna de `ADMIN_CORREO`/`ADMIN_PASSWORD`/`ADMIN_IDENTIFICACION`, **no se crea el admin** (aviso, el arranque continúa); si está y es **débil** sin admin existente, `AdminPasswordError` **sí impide el arranque** |
| `JWT_EXPIRATION_MINUTES` | Backend | `30` | No |
| `TRUSTED_PROXY_HOPS` | Backend | `0` | No con el default; valor no entero o negativo (`ge=0`) provoca error de validación de `Settings` y **sí impide el arranque** |
| `DIAGNOSTICO_IP` | Backend | `false` | No |
| `INFRA_SERVICE_URL` / `INFRA_TIMEOUT` | Backend | `http://localhost:3001` / `60` | No |

`TRUSTED_PROXY_HOPS=0` es correcto en local y pruebas, donde no hay proxies.

### Medición de `TRUSTED_PROXY_HOPS` (paso pendiente)

Sin medirlo, si el valor no coincide con los proxies reales la última entrada
de `X-Forwarded-For` (la del edge) se toma como cliente y **muchos usuarios
quedan agrupados bajo una sola clave**: los límites por IP se vuelven globales.
El límite alto de **100 fallos por IP** mitiga el impacto, pero no lo elimina.
Procedimiento pendiente, documentado en `docs/decisiones.md` y
`docs/despliegue-render.md`: activar `DIAGNOSTICO_IP=true` en producción unos
minutos, observar el conteo estable **N** de entradas, fijar **N-1** y volver a
`false`. El diagnóstico solo registra conteos y booleanos, nunca IPs.

## Pruebas

```bash
cd backend && python -m pytest          # backend (FastAPI)
cd infraestructura-service && npm test  # servicio de infraestructura (Express)
```

## Despliegue

Guía de **pasos pendientes** en
[`docs/despliegue-render.md`](docs/despliegue-render.md): nada de lo descrito
está desplegado ni probado en producción.
