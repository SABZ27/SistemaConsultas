# Guía de despliegue en Render (FastAPI + Express)

## Objetivo
Desplegar los dos servicios del monorepo en Render con sus respectivas bases de datos:
- `backend/` (FastAPI) -> PostgreSQL en **Neon**
- `infraestructura-service/` (Express) -> MySQL en **Aiven**

Ambos servicios comparten el mismo `JWT_SECRET` para validar tokens.

## Variables por servicio (solo nombres)
### Backend (FastAPI)
- `DB_URL` / `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`
- `JWT_SECRET`, `JWT_EXPIRATION_MINUTES`
- `ADMIN_CORREO`, `ADMIN_PASSWORD`, `ADMIN_IDENTIFICACION`
- `INFRA_SERVICE_URL`, `INFRA_TIMEOUT`

### Infraestructura (Express)
- `PORT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL`, `DB_CONNECTION_LIMIT`
- `JWT_SECRET`, `CORS_ORIGINS`, `TEST_DB_NAME`
- `EMAIL_PROVIDER_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`

**Importante:** `JWT_SECRET` debe ser **idéntico** en ambos servicios.

## Orden de despliegue (pasos pendientes)
1. **Respaldo**: crear una rama de respaldo en **Neon** (snapshot/backup) antes de aplicar cambios.
2. **Migración**: aplicar `backend/migrations/005_infraestructura_postgres.sql` en **Neon** (migración 005). Esta migración mueve la infraestructura física a PostgreSQL, limpia las referencias heredadas de MySQL y crea la FK `fk_solicitudes_recurso_fisico`.
3. **Inicialización Aiven**: ejecutar `db:init` en **Aiven/MySQL** **sin** `--drop-legacy` para crear el esquema de servicios externos (`servicios_externos`, `consultas_servicio_externo`, `festivos`, `correos_enviados`) y sembrar `Nager.Date` y `Brevo`.
4. **Variables Express**: configurar en Express `EMAIL_PROVIDER_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME` (junto con las variables ya existentes). Asegurar que `JWT_SECRET` sea idéntico al backend.
5. **Despliegue**: hacer push (pendiente de autorización) y esperar a que **ambos** servicios estén `Live` en Render.
6. **Pruebas de humo**: verificar autenticación, validación de festivo al crear/reprogramar una solicitud, envío de correo con token `rol=SERVICIO` (Express rechaza tokens de usuario con 403), y creación/asignación de recursos físicos en FastAPI.
7. **Limpieza legacy (solo al final)**: ejecutar `db:init --drop-legacy` **únicamente** si ya no es necesario conservar las tablas legacy (`sedes`, `zonas`, `recursos_fisicos`) en MySQL. Este paso es opcional y debe hacerse al final, tras confirmar que todo funciona.

## Notas
- No incluir credenciales en el repositorio. Solo se documentan nombres de variables.
- Usar conexiones SSL cuando lo exija el proveedor (Neon/Aiven).
- El servicio Express solo gestiona servicios externos (festivos/correos) y bitácora; la infraestructura física vive en PostgreSQL (FastAPI).
- El despliegue descrito son **pasos pendientes** (no se afirma que ya esté desplegado o probado en producción).
- Los arranques en frío pueden ocurrir en planes gratuitos; `INFRA_TIMEOUT=60` en FastAPI tolera el *cold start* de Express.
