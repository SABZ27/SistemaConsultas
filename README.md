# Sistema de Gestión de Consultas Académicas

Sistema para gestionar consultas académicas entre estudiantes, docentes y
administradores, con autenticación JWT basada en roles y módulos del sistema.

El monorepo tiene dos servicios que se despliegan por separado en **Render**:

| Servicio | Stack | Base de datos |
|---|---|---|
| `backend/` | FastAPI + SQLAlchemy + Uvicorn (Python 3.13) | PostgreSQL (Neon) |
| `infraestructura-service/` | Express + Node 24 | MySQL (Aiven) |

## Arquitectura final

- **PostgreSQL (Neon)**: contiene **19 tablas** del dominio de negocio, incluyendo `sedes`, `zonas` y `recursos_fisicos` con claves foráneas hacia `solicitudes_consultas` (`recurso_fisico_id`).
- **MySQL (Aiven)**: contiene las **4 tablas** de servicios externos (`servicios_externos`, `consultas_servicio_externo`, `festivos`, `correos_enviados`) con las relaciones definidas entre ellas.
- **FastAPI (backend)**: expone endpoints del dominio, incluyendo `/sedes`, `/zonas`, `/recursos-fisicos`. Valida fechas festivas al crear y reprogramar solicitudes, llamando al microservicio de servicios externos.
- **Express (infraestructura-service)**: expone servicios externos en `/festivos`, `/correos`, `/servicios-externos`. `POST /correos` solo acepta tokens con rol `SERVICIO`. Usa **Nager.Date** para festivos y **Brevo** para envío de correos transaccionales.

## Roles

- **ESTUDIANTE**: crea y da seguimiento a sus consultas, comenta y califica.
- **DOCENTE**: atiende consultas, gestiona su disponibilidad y asigna recursos.
- **ADMINISTRADOR**: administra usuarios, roles/módulos, catálogos y solicitudes.

El acceso a cada funcionalidad se controla por el rol y por los módulos del
sistema asignados a ese rol (claim `modulos` del JWT).

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
variables y valores de ejemplo (nunca reales):

- `backend/.env.example`: `DB_URL`, `DB_HOST`, `DB_PORT`, `DB_USERNAME`,
  `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, `JWT_EXPIRATION_MINUTES`,
  `ADMIN_CORREO`, `ADMIN_PASSWORD`, `ADMIN_IDENTIFICACION`,
  `INFRA_SERVICE_URL`, `INFRA_TIMEOUT`.
- `infraestructura-service/.env.example`: `PORT`, `DB_HOST`, `DB_PORT`,
  `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL`, `DB_CONNECTION_LIMIT`,
  `JWT_SECRET`, `CORS_ORIGINS`, `TEST_DB_NAME`, `EMAIL_PROVIDER_API_KEY`,
  `EMAIL_FROM`, `EMAIL_FROM_NAME`.

`JWT_SECRET` debe usar el mismo valor (mínimo 32 caracteres) en ambos servicios.

## Pruebas

```bash
cd backend && python -m pytest          # backend (FastAPI)
cd infraestructura-service && npm test  # servicio de infraestructura (Express)
```

## Despliegue

Guía paso a paso en [`docs/despliegue-render.md`](docs/despliegue-render.md).
