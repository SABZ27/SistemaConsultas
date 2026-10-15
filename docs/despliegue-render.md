# Despliegue en Render

Guía para publicar el Sistema de Consultas en [Render](https://render.com). El
monorepo tiene **dos servicios** que se despliegan por separado y usan bases de
datos externas gestionadas:

```
                 ┌────────────────────────┐      ┌──────────────────────────┐
  Cliente  ───▶  │  backend (FastAPI)      │ ───▶ │  infraestructura-service │
                 │  Python 3.13 + Uvicorn  │ HTTP │  Node 24 + Express       │
                 └───────────┬────────────┘      └────────────┬─────────────┘
                             │                                 │
                             ▼                                 ▼
                    PostgreSQL (Neon)                    MySQL (gestionado)
                    base: sistema_consultas              base: sistema_consultas_infra
```

> No hay que crear ninguna base de datos en Render: FastAPI usa **PostgreSQL
> (Neon)** y Express usa un **MySQL gestionado** (p. ej. PlanetScale, Aiven,
> Railway o el MySQL de tu proveedor). Solo se configuran las cadenas de conexión.

---

## 1. Preparación previa

1. Ten a mano la **cadena de conexión de PostgreSQL** (Neon) y la de **MySQL**.
2. Genera **un único `JWT_SECRET`** (mínimo 32 caracteres) y úsalo **idéntico** en
   ambos servicios; si no coincide, el backend FastAPI no podrá autenticarse
   contra Express (obtendrá `401`).
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
3. Define las credenciales del **administrador inicial** del backend
   (`ADMIN_CORREO`, `ADMIN_PASSWORD`, `ADMIN_IDENTIFICACION`). La semilla se ejecuta
   al arrancar y solo crea el usuario si **no existe ningún administrador**.

---

## 2. Servicio `infraestructura-service` (Express + MySQL)

| Ajuste | Valor |
|---|---|
| **Language / Runtime** | Node |
| **Root Directory** | `infraestructura-service` |
| **Build Command** | `npm ci` |
| **Start Command** | `npm start` |
| **Node version** | `24.x` (fijada en `package.json` → `engines`) |

El proceso escucha en `process.env.PORT` (Render lo inyecta en `PORT`). En local,
`PORT` por defecto es `3001`.

El servicio ya expone **`GET /health`** (sin autenticación) para el *health check*
de Render.

### Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `JWT_SECRET` | Sí | Mismo valor que en el backend FastAPI (HS256). |
| `DB_HOST` | Sí | Host del MySQL gestionado. |
| `DB_PORT` | Sí | Puerto del MySQL (p. ej. `3306` o el del proveedor). |
| `DB_USER` | Sí | Usuario de MySQL. |
| `DB_PASSWORD` | Sí | Contraseña de MySQL. |
| `DB_NAME` | Sí | Base de infraestructura (`sistema_consultas_infra`). |
| `DB_SSL` | Según proveedor | `true` para MySQL gestionado que exige TLS; `false` en local. |
| `DB_CONNECTION_LIMIT` | No | Tamaño del pool (por defecto `10`). |
| `CORS_ORIGINS` | Sí | Orígenes permitidos separados por comas (no uses `*` en producción). |
| `PORT` | — | Lo inyecta Render. No lo definas a mano. |

### Crear las tablas (una sola vez)

El esquema está en `sql/schema.sql`. El comando `npm run db:init` crea la base y
las tablas, pero **necesita conectividad** al MySQL; si el proveedor no permite
conexiones desde tu PC, aplica `sql/schema.sql` con la consola del proveedor.

```bash
cd infraestructura-service
# Con las variables DB_* del MySQL real en el entorno o en .env:
npm run db:init
```

---

## 3. Servicio `backend` (FastAPI + PostgreSQL/Neon)

| Ajuste | Valor |
|---|---|
| **Language / Runtime** | Python |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Python version** | `3.13.14` (fijada en `backend/.python-version`) |

El `backend/Procfile` ya contiene el *start command* anterior, de modo que Render
lo detecta automáticamente. En local, arranca en el puerto `8080`:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

`uvicorn[standard]` ya está incluido en `requirements.txt`.

### Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DB_URL` | Sí* | Cadena de Neon, p. ej. `postgresql://usuario:clave@<HOST_NEON_VERIFICACION>/neondb?sslmode=require`. |
| `DB_HOST`/`DB_PORT`/`DB_USERNAME`/`DB_PASSWORD`/`DB_NAME` | Sí* | Configuración por partes (solo si `DB_URL` está vacía). |
| `JWT_SECRET` | Sí | Mismo valor que en `infraestructura-service`. |
| `JWT_EXPIRATION_MINUTES` | No | Duración del token (por defecto `30`). |
| `ADMIN_CORREO` | Sí | Correo del administrador inicial. |
| `ADMIN_PASSWORD` | Sí | Contraseña del administrador inicial. |
| `ADMIN_IDENTIFICACION` | Sí | Identificación del administrador inicial. |
| `INFRA_SERVICE_URL` | Sí | URL pública del servicio Express (con `https://`). |
| `INFRA_TIMEOUT` | No | Timeout (segundos) de las llamadas a Express; por defecto `60` (tolera el *cold start*). |

\* Usa `DB_URL` **o** la configuración por partes; `DB_URL` tiene prioridad.

FastAPI aplica las **migraciones de SQLAlchemy** al arrancar y luego ejecuta la
semilla idempotente del administrador.

---

## 4. Orden de despliegue

1. **PostgreSQL (Neon)**: crea la base `sistema_consultas` (Neon ya crea `neondb`).
2. **MySQL gestionado**: crea la base `sistema_consultas_infra` y aplica
   `infraestructura-service/sql/schema.sql`.
3. Despliega **`infraestructura-service`** (Express) y espera a que su
   `GET /health` responda `200`.
4. Copia la URL pública de Express y configúrala en el backend como
   `INFRA_SERVICE_URL`.
5. Despliega **`backend`** (FastAPI). Al arrancar creará las tablas y el admin.

---

## 5. Prueba de humo

```bash
# 1) Express: estado del servicio
curl https://<infra-service>.onrender.com/health          # -> {"status":"ok"}

# 2) FastAPI: inicio de sesión con el administrador sembrado
curl -X POST https://<backend>.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo":"<ADMIN_CORREO>","password":"<ADMIN_PASSWORD>"}'   # -> { "access_token": "..." }

# 3) FastAPI -> Express: resolver un recurso de infraestructura con el token
curl https://<backend>.onrender.com/... -H "Authorization: Bearer <access_token>"
```

Si el paso 3 devuelve `503`, el backend no puede alcanzar Express: revisa
`INFRA_SERVICE_URL`, que Express esté despierto y que `JWT_SECRET` coincida.

---

## 6. Arranques en frío (cold starts)

Los planes gratuitos suspenden los servicios por inactividad. El primer request
puede tardar bastante:

- `INFRA_TIMEOUT=60` en FastAPI (1 reintento automático) absorbe el despertar de
  Express.
- **Despierta ambos servicios antes de probar** (abre sus `GET /health` en el
  navegador) para que la primera petición real no expire.

---

## 7. Reiniciar la base de PostgreSQL (solo si hace falta)

Para empezar de cero el esquema de Neon, ejecuta **manualmente** en el SQL Editor
de Neon (no lo hagas desde la app):

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

Al reiniciar el backend, volverá a crear las tablas y el administrador inicial.
