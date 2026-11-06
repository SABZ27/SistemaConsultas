# Guía de despliegue en Render (FastAPI + Express) — pasos pendientes

## Objetivo

Desplegar los dos servicios del monorepo en Render con sus respectivas bases
de datos:

- `backend/` (FastAPI) -> PostgreSQL en **Neon**
- `infraestructura-service/` (Express) -> MySQL en **Aiven**

Ambos servicios comparten el mismo `JWT_SECRET` para validar tokens.

> **Todo lo descrito aquí son pasos pendientes.** No se ha desplegado ni probado
> nada en producción. El push y el despliegue los realiza el responsable del
> proyecto; esta guía solo documenta el orden previsto.

## Variables por servicio (solo nombres)

### Backend (FastAPI)
- `DB_URL` / `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`
- `JWT_SECRET`, `JWT_EXPIRATION_MINUTES` (`30`)
- `ADMIN_CORREO`, `ADMIN_PASSWORD`, `ADMIN_IDENTIFICACION`
- `CORS_ORIGINS` (`http://localhost:5173,http://localhost:3000`)
- `INFRA_SERVICE_URL` (`http://localhost:3001`), `INFRA_TIMEOUT` (`60`)
- `TRUSTED_PROXY_HOPS` (`0`), `DIAGNOSTICO_IP` (`false`)

### Infraestructura (Express)
- `PORT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL`, `DB_CONNECTION_LIMIT`
- `JWT_SECRET`, `CORS_ORIGINS`, `TEST_DB_NAME`
- `EMAIL_PROVIDER_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`

**Importante:** `JWT_SECRET` debe ser **idéntico** en ambos servicios, tener al
menos 32 caracteres y no ser el valor de ejemplo. Solo se documentan nombres y
defaults: **no se incluyen credenciales ni valores reales**.

### Variables que pueden impedir el arranque

| Variable | Motivo |
|---|---|
| `JWT_SECRET` | <32 caracteres o igual al placeholder: `validar_jwt_secret()` (FastAPI) y `validarConfiguracion()` (Express) fallan |
| `CORS_ORIGINS` | Vacía o con `*`: `origenes_cors()` / `validarConfiguracion()` fallan (se envían credenciales) |
| `ADMIN_PASSWORD` | Si falta alguna de las tres `ADMIN_*`, **no se crea el administrador** (solo aviso, el arranque continúa). Si está presente y es débil sin administrador existente, `AdminPasswordError` **impide el arranque** |
| `TRUSTED_PROXY_HOPS` | Entero `>= 0`; un valor no entero o negativo provoca error de validación de `Settings` e **impide el arranque** |

`TRUSTED_PROXY_HOPS=0` y `DIAGNOSTICO_IP=false` son correctos en local y
pruebas; en Render deben revisarse con el procedimiento de medición siguiente.

## Medición de `TRUSTED_PROXY_HOPS` (paso pendiente)

La IP del cliente se toma de `X-Forwarded-For` en la posición
`-(TRUSTED_PROXY_HOPS + 1)` desde la derecha. **Sin medirlo**, si el valor no
coincide con los proxies reales se toma la última entrada (la del edge),
compartida por muchos clientes: **los usuarios quedan agrupados bajo una sola
clave** y los límites por IP se vuelven globales, con riesgo de `429` masivo.
El límite alto de **100 fallos por IP / 15 min** mitiga el impacto, pero no lo
elimina; los límites por pareja (5) y por correo (15) siguen activos.

Procedimiento previsto:

1. Activar `DIAGNOSTICO_IP=true` **en producción durante unos minutos** y
   volver a `false` en cuanto se observe el patrón. El diagnóstico **solo
   registra el número de entradas de `X-Forwarded-For` y si existe
   `True-Client-IP`** (conteos y booleanos), **nunca direcciones IP** ni otros
   datos personales.
2. Observar en el log el valor estable de `x_forwarded_for_entradas` = **N**
   para el tráfico normal durante esa ventana.
3. Con la convención de `X-Forwarded-For` (el cliente es la primera entrada y
   cada proxy añade la suya al final), fijar **`TRUSTED_PROXY_HOPS = N - 1`**
   en el panel de Render.
4. Repetir la medición tras cualquier cambio de topología, CDN, región o plan.
5. Confirmar que `DIAGNOSTICO_IP` quedó en `false`.

El diagnóstico solo da conteos: no muestra la cadena y no confirma por sí solo
que la primera entrada sea el cliente real. Esta resolución por saltos asume
que el servicio solo recibe tráfico a través de los proxies de Render; **no
valida la confianza de las entradas**. Detalle en `docs/decisiones.md`.

## Orden de despliegue (pasos pendientes)

1. **Respaldo**: crear una rama de respaldo en **Neon** (snapshot/backup) antes de aplicar cambios.
2. **Migración**: aplicar `backend/migrations/005_infraestructura_postgres.sql` en **Neon** (migración 005). Esta migración mueve la infraestructura física a PostgreSQL, limpia las referencias heredadas de MySQL y crea la FK `fk_solicitudes_recurso_fisico`.
3. **Inicialización Aiven**: ejecutar `db:init` en **Aiven/MySQL** **sin** `--drop-legacy` para crear el esquema de servicios externos (`servicios_externos`, `consultas_servicio_externo`, `festivos`, `correos_enviados`) y sembrar `Nager.Date` y `Brevo`.
4. **Variables**: configurar en el panel las variables de ambos servicios (incluidas `TRUSTED_PROXY_HOPS` y `DIAGNOSTICO_IP`, y `EMAIL_PROVIDER_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME` en Express). Asegurar que `JWT_SECRET` sea idéntico.
5. **Medición de proxies**: aplicar el procedimiento anterior y fijar `TRUSTED_PROXY_HOPS`.
6. **Despliegue**: hacer push (pendiente de autorización) y esperar a que **ambos** servicios estén `Live` en Render.
7. **Pruebas de humo**: verificar autenticación, validación de festivo al crear/reprogramar una solicitud, envío de correo con token `rol=SERVICIO` (Express rechaza tokens de usuario con 403), creación/asignación de recursos físicos en FastAPI y el formato de error 429/503.
8. **Paso manual — borrar las 3 tablas viejas de Aiven**: una vez comprobado que la infraestructura física vive en PostgreSQL y que ya no se necesita conservarlas, **el operador debe borrar manualmente `sedes`, `zonas` y `recursos_fisicos` en MySQL/Aiven**, con respaldo previo. Es un paso manual y opcional, **solo al final**; `db:init --drop-legacy` existe como alternativa, pero tampoco se ha ejecutado. Nada de este paso se ha realizado en este trabajo y no se ha conectado a Aiven.

## Notas

- No incluir credenciales en el repositorio. Solo se documentan nombres de variables.
- Usar conexiones SSL cuando lo exija el proveedor (Neon/Aiven).
- El servicio Express solo gestiona servicios externos (festivos/correos) y bitácora; la infraestructura física vive en PostgreSQL (FastAPI).
- Los arranques en frío pueden ocurrir en planes gratuitos; `INFRA_TIMEOUT=60` en FastAPI tolera el *cold start* de Express. La validación de festivos usa su propio timeout y es **fail-closed** con `503` si no puede validar.
- **Todos los pasos son pendientes**: no se afirma que el sistema esté desplegado, configurado ni probado en producción.
- Scripts SQL de entrega para un compañero: `docs/sql/LEEME.md`.
