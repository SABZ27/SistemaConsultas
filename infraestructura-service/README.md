# infraestructura-service

Microservicio de **infraestructura física** (sedes, zonas y recursos físicos) para el
Sistema de Consultas. Implementado con **Node 24 + Express** sobre **MySQL 8 (InnoDB, utf8mb4)**.

Forma parte del monorepo junto al backend FastAPI (`backend/`) y comparte el mismo
`JWT_SECRET`. El backend FastAPI lo consume en la Fase 4 para validar y resolver recursos.

## Modelo de datos

Tres tablas. Todas incluyen `id` (PK AUTO_INCREMENT), `estado` (TINYINT(1), default 1,
borrado lógico), `creado` y `actualizado` (gestionados por MySQL) y al menos un índice único.

- **sedes**: `nombre`, `tipo_estructura` ENUM(`BLOQUES`, `SALONES`, `PISOS`).
- **zonas** (bloque o piso según la sede): `sede_id` (FK), `nombre` ("Bloque A", "Piso 2").
- **recursos_fisicos**: `sede_id` (FK), `zona_id` (FK nullable), `nombre`, `tipo`
  ENUM(`SALON`, `LABORATORIO`, `AUDITORIO`, `SALA`, `OFICINA`).

El borrado es lógico: los índices únicos usan columnas generadas (`nombre_activo`,
`zona_key`) que valen `NULL` cuando la fila está inactiva, de modo que el nombre se libera
y puede reutilizarse. Una FK compuesta `(zona_id, sede_id) -> zonas(id, sede_id)` garantiza
que la zona pertenece a la misma sede del recurso.

### Estructuras de sede

- **BLOQUES**: la sede se divide en bloques (A, B, C…); los recursos cuelgan de un bloque.
- **SALONES**: sin subdivisión; los recursos (Salón 1 al 30) cuelgan directo de la sede.
- **PISOS**: el edificio se divide en pisos; los recursos cuelgan de un piso.

Ejemplo de referencia (solo documentación/tests): sede **"Granadillo"**, tipo `PISOS`,
Piso 1 a Piso 5 con Salón 1 a Salón 6 en cada piso.

## Instalación

Requiere Node 24+ y MySQL 8.

```bash
cd infraestructura-service
cp .env.example .env      # completa DB_* y JWT_SECRET
npm install
```

### MySQL con Docker (recomendado para desarrollo)

```bash
docker compose up -d mysql
# El contenedor monta sql/schema.sql y crea la base automáticamente.
```

### MySQL local

```bash
npm run db:init           # crea la base (DB_NAME) y las tablas
```

No se siembran datos: sedes, zonas y recursos nacen vacíos.

## Ejecución

```bash
npm start                 # http://localhost:3001
npm run dev               # recarga automática (node --watch)
```

`GET /health` no requiere autenticación. El resto de rutas exigen `Authorization: Bearer <jwt>`.

## Autenticación y autorización

- El JWT es HS256 y se firma con `JWT_SECRET` (el mismo que el backend FastAPI).
- **Lecturas**: cualquier token válido.
- **Escrituras** (POST/PUT/DELETE/PATCH y `?incluir_inactivos=true`): el claim `modulos`
  debe incluir `INFRAESTRUCTURA`; si no, `403`.
- Sin token o token inválido: `401`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio (sin auth). |
| GET | `/sedes` | Lista de sedes (`?incluir_inactivos=true`). |
| GET | `/sedes/:id` | Detalle de una sede. |
| POST | `/sedes` | Crea una sede. |
| PUT | `/sedes/:id` | Actualiza nombre y tipo de estructura. |
| DELETE | `/sedes/:id` | Borrado lógico (`estado=0`, 204). |
| PATCH | `/sedes/:id/activar` | Reactiva la sede. |
| GET | `/sedes/:id/zonas` | Zonas de la sede. |
| GET | `/sedes/:id/recursos-fisicos` | Recursos de la sede. |
| GET | `/sedes/:id/estructura` | Árbol de la sede (404 si no existe). |
| GET/POST | `/zonas` | Lista (filtro `?sedeId=`) y crea zonas. |
| GET/PUT/DELETE | `/zonas/:id` | Detalle, actualización y borrado lógico. |
| PATCH | `/zonas/:id/activar` | Reactiva la zona. |
| GET | `/zonas/:id/recursos-fisicos` | Recursos de la zona. |
| GET/POST | `/recursos-fisicos` | Lista (filtros `?sedeId=`, `?zonaId=`) y crea recursos. |
| GET/PUT/DELETE | `/recursos-fisicos/:id` | Detalle, actualización y borrado lógico. |
| PATCH | `/recursos-fisicos/:id/activar` | Reactiva el recurso. |

### Reglas de negocio (400 con mensaje claro)

- Sede `BLOQUES`/`PISOS`: el recurso exige `zonaId` de esa sede.
- Sede `SALONES`: no admite zonas; los recursos no pueden tener `zonaId`.
- `tipoEstructura` solo cambia si la sede no tiene zonas ni recursos activos.
- No se desactiva una sede con zonas o recursos activos, ni una zona con recursos activos.

### Respuesta de un recurso

```json
{
  "id": 1,
  "nombre": "Salón 3",
  "tipo": "SALON",
  "estado": true,
  "sedeId": 1,
  "sedeNombre": "Granadillo",
  "zonaId": 2,
  "zonaNombre": "Piso 2",
  "ubicacion": "Granadillo · Piso 2 · Salón 3"
}
```

## Ejemplos con curl

```bash
# Token de ejemplo (para pruebas locales). En producción lo emite FastAPI.
TOKEN=$(node -e "console.log(require('jsonwebtoken').sign({sub:'a@b.c',uid:1,rol:'ADMINISTRADOR',modulos:['INFRAESTRUCTURA']}, process.env.JWT_SECRET, {expiresIn:'30m'}))")

curl http://localhost:3001/health

curl -X POST http://localhost:3001/sedes \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nombre":"Granadillo","tipoEstructura":"PISOS"}'

curl -X POST http://localhost:3001/zonas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sedeId":1,"nombre":"Piso 2"}'

curl -X POST http://localhost:3001/recursos-fisicos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sedeId":1,"zonaId":1,"nombre":"Salón 3"}'

curl http://localhost:3001/sedes/1/estructura -H "Authorization: Bearer $TOKEN"
```

## Tests

```bash
npm test
```

`jest + supertest` levantan la app y usan una base de datos de pruebas. El nombre
de la base es **`TEST_DB_NAME`** (por defecto `sistema_consultas_infra_test`) y cada
worker de Jest recibe su propia base (`<test>_w<N>_test`), de modo que la suite
funciona igual con `--runInBand` (serial) y en paralelo.

La base del worker se crea y se le aplica `sql/schema.sql` de forma automática
antes de cada archivo de test; cada suite limpia las tablas antes de cada prueba y
crea sus propios datos. El nombre de la base debe terminar en `_test`; si no, el
arranque aborta con un error claro (nunca se crea ni se borra una base que no sea
de pruebas). Si MySQL no está disponible, la suite **falla** (no se omite en silencio).

Cubren: autenticación/autorización, CRUD, borrado lógico y únicos con reactivación,
tablas vacías y las tres estructuras (con el ejemplo de Granadillo) y sus reglas.

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
`sql/schema.sql` (o `npm run db:init`).
