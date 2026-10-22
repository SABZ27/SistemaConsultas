# infraestructura-service

Microservicio de **servicios externos** para el Sistema de Consultas. Implementado con
**Node 24 + Express** sobre **MySQL 8 (InnoDB, utf8mb4)**.

Responsabilidades:

- **Días festivos** desde la API pública de **Nager.Date** (`https://date.nager.at/api/v4`).
- **Envío de correo** desde la **API HTTP de Brevo** (`https://api.brevo.com/v3`), nunca SMTP.
- **Bitácora** de cada llamada a un proveedor externo.

La infraestructura física (sedes, zonas y recursos físicos) vive en **PostgreSQL dentro del
backend FastAPI** (`backend/`); este servicio ya no la administra.

## Modelo de datos

Cuatro tablas. Todas incluyen `id` (PK AUTO_INCREMENT), `estado` (TINYINT(1), default 1,
borrado lógico), `creado` y `actualizado` (gestionados por MySQL).

- **servicios_externos**: catálogo de proveedores. `nombre` (único, es la clave lógica:
  `Nager.Date` o `Brevo`), `url_base`, `descripcion`.
- **consultas_servicio_externo**: bitácora de las llamadas. `servicio_id` (FK),
  `referencia` (UUID), `endpoint`, `codigo_http`, `exito`, `duracion_ms`, `detalle`.
- **festivos**: cache local de los festivos. `servicio_id` (FK), `consulta_servicio_id` (FK
  nullable), `fecha`, `pais`, `nombre` (en español), `anio`. Único `UNIQUE (fecha, pais)`.
- **correos_enviados**: `servicio_id` (FK), `consulta_servicio_id` (FK, único),
  `destinatario`, `asunto`, `estado_envio` ENUM(`ENVIADO`, `FALLIDO`), `respuesta_proveedor`.

El esquema completo está en [`sql/schema.sql`](sql/schema.sql) y es idempotente
(`CREATE TABLE IF NOT EXISTS`).

### Reglas de negocio

- Los proveedores se buscan **por nombre** (`Nager.Date`, `Brevo`); si la fila no existe o
  está inactiva el servicio responde **503**.
- Cada llamada externa inserta su fila en `consultas_servicio_externo` **después** de la
  llamada; su `id` es al que apuntan `festivos.consulta_servicio_id` y
  `correos_enviados.consulta_servicio_id`.
- Un error de red (sin respuesta) **también se registra**: `codigo_http` NULL, `exito = 0`,
  `detalle = 'sin respuesta'`; el correo queda en `FALLIDO` y la API responde **502**.
- El `detalle` es un texto breve y saneado: nunca se guardan correos ni datos personales.
- La cache de festivos se filtra siempre por `pais` + `anio` + `estado = 1`. El `upsert`
  usa `UNIQUE (fecha, pais)` y **nunca cambia `estado`**: un festivo desactivado no se
  resucita al resincronizar y no se vuelve a llamar al proveedor.
- El borrado de un festivo es lógico (`estado = 0`) y **solo lo puede hacer el rol
  `ADMINISTRADOR`**; el resto de usuarios recibe **403**.
- `POST /correos` lo puede usar **cualquier usuario autenticado**.

### Corrección Ley Emiliani sobre datos de Nager.Date

En Colombia los festivos eclesiásticos móviles se observan el **lunes siguiente**
(Ley Emiliani, Ley 51 de 1883 y determinaciones del Ministerio del Interior), no el día de
la plegaria. Nager.Date devuelve el día de la plegaria, por ejemplo para 2026:

| Festivo | Nager.Date (plegaria) | Fecha oficial (lunes) |
|---|---|---|
| `Ascension Day` | 2026-05-14 (jueves) | **2026-05-18** |
| `Corpus Christi` | 2026-06-04 (jueves) | **2026-06-08** |

El servicio corrige **solo** esos dos festivos: si la fecha no cae en lunes se mueve al
lunes siguiente antes de guardarse (actualizando también el año si el traslado cruza el
cambio de año). Ningún otro festivo se modifica (por ejemplo `Sacred Heart` ya lo publica
el lunes, 2026-06-15). La lógica vive en [`src/utils/leyEmiliani.js`](src/utils/leyEmiliani.js).

## Instalación

Requiere Node 24+ y MySQL 8.

```bash
cd infraestructura-service
cp .env.example .env      # completa DB_*, JWT_SECRET y EMAIL_*
npm install
```

### MySQL con Docker (recomendado para desarrollo)

```bash
docker compose up -d mysql
```

### MySQL local

```bash
npm run db:init           # crea la base, aplica sql/schema.sql y siembra los proveedores
```

`npm run db:init` siembra los dos proveedores (idempotente, no toca su `estado`):

| nombre | url_base | descripcion |
|---|---|---|
| `Nager.Date` | `https://date.nager.at/api/v4` | API pública de festivos por país |
| `Brevo` | `https://api.brevo.com/v3` | API de correo transaccional |

Las tablas de la infraestructura física (`sedes`, `zonas`, `recursos_fisicos`) ya no se
administran desde aquí. Para eliminarlas de una base existente hace falta la confirmación
explícita del responsable del proyecto:

```bash
npm run db:init -- --drop-legacy
```

## Ejecución

```bash
npm start                 # http://localhost:3001
npm run dev               # recarga automática (node --watch)
```

`GET /health` no requiere autenticación. El resto de rutas exigen `Authorization: Bearer <jwt>`.

## Autenticación y autorización

- El JWT es HS256 y se firma con `JWT_SECRET` (el mismo que el backend FastAPI).
- Sin token o token inválido: `401`.
- `DELETE /festivos/:id` exige el rol `ADMINISTRADOR` (`claim rol`); si no, `403`.
- El resto de rutas exige únicamente un token válido.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio (sin auth). |
| GET | `/festivos` | Festivos del año (`?anio=YYYY&pais=CO`). Sincroniza con Nager.Date si el año no está en cache. |
| GET | `/festivos/validar` | Valida una fecha (`?fecha=YYYY-MM-DD&pais=CO`). |
| DELETE | `/festivos/:id` | Borrado lógico del festivo (`estado=0`, 204). Solo `ADMINISTRADOR`. |
| POST | `/correos` | Envía un correo por la API de Brevo (201). Cualquier usuario autenticado. |
| GET | `/servicios-externos` | Lista los proveedores configurados (solo activos). |

### Respuestas

```json
// GET /festivos/validar?fecha=2026-05-18
{ "id": 7, "fecha": "2026-05-18", "pais": "CO", "esFestivo": true, "nombre": "Ascensión del Señor" }

// GET /festivos/validar?fecha=2026-05-14
{ "fecha": "2026-05-14", "pais": "CO", "esFestivo": false, "nombre": null, "id": null }

// POST /correos
{ "id": 12, "messageId": "<abc123@ejemplo.com>", "estadoEnvio": "ENVIADO" }
```

### Códigos de error relevantes

- `400` — petición inválida (validación con `zod`).
- `401` — sin token o token inválido.
- `403` — el rol no permite la acción (borrado de festivo).
- `404` — festivo inexistente.
- `502` — el proveedor externo falló (se registró la llamada en la bitácora).
- `503` — el proveedor no está configurado en `servicios_externos` o falta la API key.

## Ejemplos con curl

```bash
TOKEN=$(node -e "console.log(require('jsonwebtoken').sign({sub:'a@b.c',uid:1,rol:'ADMINISTRADOR'}, process.env.JWT_SECRET, {expiresIn:'30m'}))")

curl http://localhost:3001/health

curl "http://localhost:3001/festivos/validar?fecha=2026-05-18" -H "Authorization: Bearer $TOKEN"

curl "http://localhost:3001/festivos?anio=2026" -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:3001/correos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"para":"destinatario@ejemplo.com","asunto":"Confirmación","contenido":"Su solicitud fue registrada."}'

curl -X DELETE http://localhost:3001/festivos/7 -H "Authorization: Bearer $TOKEN"
```

## Tests

```bash
npm test
```

`jest + supertest` levantan la app y usan una base de datos de pruebas. El nombre de la
base es **`TEST_DB_NAME`** (por defecto `sistema_consultas_infra_test`) y cada worker de
Jest recibe su propia base (`<test>_w<N>_test`), de modo que la suite funciona igual con
`--runInBand` (serial) y en paralelo.

La base del worker se crea y se le aplica `sql/schema.sql` de forma automática antes de
cada archivo de test; cada suite limpia las tablas y vuelve a sembrar los proveedores
antes de cada prueba. El nombre de la base debe terminar en `_test`; si no, el arranque
aborta con un error claro (nunca se crea ni se borra una base que no sea de pruebas). Si
MySQL no está disponible, la suite **falla** (no se omite en silencio).

**Las pruebas nunca salen a la red**: `global.fetch` se simula con `tests/fixtures/nagerCo2026.js`,
que es una copia de la respuesta real de `https://date.nager.at/api/v4/Holidays/CO/2026`.

Cubren: autenticación/autorización, sincronización con Nager.Date, bitácora de llamadas,
corrección Ley Emiliani (incluido el cambio de año), festivo desactivado que no se
resucita ni se resincroniza, error de red y 5xx con reintento (y 404 sin reintento), envío
de correo con la API de Brevo (éxito, error de red y error del proveedor) y el listado de
proveedores.

## Formato de errores

Igual que el backend FastAPI:

```json
{
  "timestamp": "2026-01-01T00:00:00.000Z",
  "status": 403,
  "error": "Forbidden",
  "message": "No tiene permisos para realizar esta acción.",
  "errors": null
}
```

## Despliegue

```bash
docker build -t infraestructura-service .
docker run --env-file .env -p 3001:3001 infraestructura-service
```

Configura `CORS_ORIGINS` con la lista de orígenes permitidos (separados por comas) y
`JWT_SECRET` con el mismo valor que FastAPI. La base de datos debe crearse una vez con
`sql/schema.sql` (o `npm run db:init`). La **API key de Brevo** solo se lee de
`EMAIL_PROVIDER_API_KEY`: nunca se guarda en la base de datos ni se expone por la API.
