# Verificación local contra bases reales

Fecha: 2026-10-15
Rama: `parcial-backend` (sin push, sin despliegue).
Alcance: Pasos B, C, D, E, F, H e I del encargo de verificación (Paso A ya estaba hecho; Paso G omitido).
Rerun autorizado: B y C contra Neon PostgreSQL, E y F con FastAPI apuntando a PostgreSQL, y suite Jest de Express contra MySQL local.

## Entorno y versiones

| Componente | Versión |
|---|---|
| Sistema operativo | Windows (PowerShell 5.1) |
| Python | 3.13.14 |
| FastAPI | 0.115.0 |
| Uvicorn | 0.30.6 |
| Pydantic | 2.11.3 |
| SQLAlchemy | 2.0.54 |
| psycopg | 3.3.6 |
| httpx | 0.28.1 |
| PyJWT | 2.15.1 |
| Node.js | v24.19.0 |
| Express | 4.22.3 |
| mysql2 | 3.24.5 |
| zod | 3.25.76 |
| jsonwebtoken | 9.0.3 |
| MySQL Server | 8.0.41 (puerto 3307) |
| PostgreSQL | 18.6 (Neon, solo remoto) |
| Docker | no instalado |

Bases usadas (por paso):

| Paso | Servicio | Motor / base | Detalle |
|---|---|---|---|
| B, C | FastAPI | **PostgreSQL** | `DB_URL_VERIF` (Neon, proyecto `sistema_consultas_verif`) — host `<HOST_NEON_VERIFICACION>`, base `neondb` |
| D | Express | MySQL local | `sistema_consultas_infra_verif` (termina en `_verif`) |
| E, F | FastAPI | **PostgreSQL** | `DB_URL_VERIF` (Neon, base `neondb`) |
| E, F | Express | MySQL local | `sistema_consultas_infra_verif` |
| Jest | Express | MySQL local | `sistema_consultas_infra_test` y `sistema_consultas_infra_w1..w8_test` (terminan en `_test`) |

Notas de seguridad de la verificación:
- Antes de cualquier DDL se comprobó que el host de `DB_URL_VERIF` contiene `<HOST_NEON_VERIFICACION>`; se abortaría si no.
- No se usó `backend/.env`. El `JWT_SECRET` de FastAPI se tomó de `infraestructura-service/.env` y se pasó por variable de entorno sin imprimirlo.
- No hubo error de `channel_binding`; la conexión a Neon funcionó sin ajustes.
- No se hizo push ni despliegue.

## Resumen de resultados

| Paso | Descripción | Base usada | Resultado |
|---|---|---|---|
| A | Detección de entorno (MySQL 3307, PostgreSQL, Docker) | — | ✔ (hecho previamente) |
| B | Esquema PostgreSQL desde cero + `verificar_esquema.py` (16 tablas) | PostgreSQL (Neon) | ✔ 16 tablas + trigger DDL |
| C | Comportamiento PostgreSQL (trigger, únicos parciales, CHECKs, idempotencia, matriz) | PostgreSQL (Neon) | ✔ 18/18 |
| D | MySQL `_verif`: 3 tablas, columnas generadas, FK compuesta, ON UPDATE, 3 estructuras, unicidad | MySQL `_verif` | ✔ 12/12 + DDL verificado |
| E | Flujo e2e con ambos servicios | PostgreSQL + MySQL `_verif` | ✔ 22/22 + caído 503 1/1 |
| F | Sondas de seguridad | PostgreSQL + MySQL `_verif` | ✔ 20/20 |
| G | (omitido a propósito) migraciones 001–003 contra bases reales | — | — |
| H | Corrección de bugs encontrados | — | ✔ Sin bugs que corregir |
| I | Documentación | — | ✔ este documento |
| J | Suite Jest de Express (`npm test`) | MySQL `_test` | ✔ 8 suites / 46 tests con y sin `--runInBand` |

## Paso B — PostgreSQL desde cero (`DB_URL_VERIF`, base `neondb`)

La base estaba vacía (0 tablas). El esquema se creó arrancando FastAPI (`app.db.session.init_db`, que ejecuta `Base.metadata.create_all`, crea los 16 triggers `trg_<tabla>_actualizado` y corre las semillas idempotentes).

Comandos:
- `python -c "from app.db.session import init_db; init_db()"` (en `backend/`, con `DB_URL=$env:DB_URL_VERIF`).
- `python scripts/verificar_esquema.py` (con `DB_URL=$env:DB_URL_VERIF`).

Resultado:
- `verificar_esquema.py` → `OK: 16 tablas verificadas` (tuvo la ADVERTENCIA esperada por contener "neon" en la URL; autorizado).
- 16 tablas `BASE TABLE` en `public`: `calificaciones_consulta, comentarios, disponibilidad_docente, docentes_modulos, eventos_solicitud, modulos, modulos_sistema, modulos_x_rol, notificaciones, password_reset_tokens, periodos_academicos, programas_academicos, roles, solicitudes_consultas, tipos_documento, usuarios`.
- 16 triggers `trg_<tabla>_actualizado` creados por `init_db`.

## Paso C — Comportamiento PostgreSQL (18/18)

Verificado directamente contra Neon (y sin escribir salvo filas temporales que se limpian):

| # | Verificación | Resultado |
|---|---|---|
| C1 | 16 tablas y conjunto exacto esperado | ✔ |
| C2 | 16 triggers `trg_*_actualizado` creados | ✔ |
| C3 | 13 índices únicos (los `uq_*`) existen | ✔ |
| C4 | Los 13 índices únicos son **parciales** (`WHERE`) | ✔ |
| C5 | CHECK `ck_calificaciones_consulta_puntaje` (1..5) | ✔ |
| C6 | CHECK `ck_disponibilidad_docente_dia_semana` (1..7) | ✔ |
| C7 | CHECK `ck_disponibilidad_docente_horas` (`hora_fin > hora_inicio`) | ✔ |
| C8 | CHECK `ck_periodos_academicos_rango` (`fecha_fin > fecha_inicio`) | ✔ |
| C9 | Trigger funcional: `UPDATE` cambia `actualizado` y conserva `creado` | ✔ |
| C10 | Único parcial funcional: duplicar correo activo → `IntegrityError`; inactivo permitido | ✔ |
| C11 | CHECK funcional: periodo con rango invertido rechazado | ✔ |
| C12 | CHECK funcional: `dia_semana=8` rechazado | ✔ |
| C13 | CHECK funcional: `hora_fin <= hora_inicio` rechazado | ✔ |
| C14 | CHECK funcional: `puntaje=6` rechazado | ✔ |
| C15 | Idempotencia de semillas (segunda ejecución no altera conteos) | ✔ |
| C16 | Matriz `modulos_x_rol` == `MATRIZ_MODULOS_X_ROL` | ✔ |

Conteos tras dos ejecuciones de semillas: roles 3, modulos_sistema 15, modulos_x_rol 24, tipos_documento 4, periodos_academicos 1, usuarios 1 (idénticos: semillas idempotentes).

## Paso D — MySQL (`sistema_consultas_infra_verif`)

Ejecutado en la verificación previa (se mantiene):

- `npm run db:init` (en `infraestructura-service/`) → crea la base y aplica `sql/schema.sql`.
- Columnas generadas confirmadas en el DDL: `sedes.nombre_activo`, `zonas.nombre_activo`, `recursos_fisicos.nombre_activo` y `zona_key` STORED; `UNIQUE` parciales/compuestos; FK compuesta `fk_recursos_zona_sede (zona_id, sede_id) → zonas(id, sede_id)`; `actualizado ... ON UPDATE CURRENT_TIMESTAMP`.
- Pruebas por API (`scripts/infra_estructuras.py`, 12/12): 3 estructuras (PISOS/BLOQUES/SALONES), ubicación completa copiada, duplicado activo → 400, borrado lógico y reinserción → 201, zona de otra sede → 400.

## Paso E — Flujo de extremo a extremo

Script: `scripts/e2e.py`. FastAPI con **`DB_URL=DB_URL_VERIF` (PostgreSQL Neon)** e `INFRA_SERVICE_URL=http://127.0.0.1:3001`; Express sobre MySQL `sistema_consultas_infra_verif`; mismo `JWT_SECRET` (de `infraestructura-service/.env`).

- Modo `full` (**22/22 OK**): login admin; admin con módulo INFRAESTRUCTURA; crear sede PISOS → piso → salón en Express; registrar docente y estudiante; asignar docente-módulo; crear periodo académico; crear disponibilidad; el estudiante crea la solicitud (PENDIENTE); asignar el recurso físico (FastAPI reenvía el Bearer a Express y guarda la `ubicacion`); transiciones válidas PENDIENTE → EN_PROCESO → RESUELTA; comentario del estudiante y del docente; calificación del estudiante tras RESUELTA; promedio del docente (`promedio=5.0`, `total=1`); notificaciones; y sonda "sin módulo INFRAESTRUCTURA → 403" al escribir en Express.
- Modo `caido` (**1/1 OK**): con Express detenido, asignar recurso responde `503` "Servicio de infraestructura no disponible".

## Paso F — Sondas de seguridad

Script: `scripts/seguridad.py` (require `ADMIN_CORREO`, `ADMIN_PASSWORD`, `JWT_SECRET`). Todas pasaron (**20/20**) contra FastAPI en PostgreSQL Neon y Express en MySQL `_verif`:

| # | Sonda | Resultado |
|---|---|---|
| F1 | Registro con rol `ADMINISTRADOR` rechazado | ✔ 403 |
| F2 | Estudiante `POST /programas` | ✔ 403 |
| F3 | Estudiante `DELETE /usuarios/{admin}` | ✔ 403 |
| F4 | Sin token → 401 en `GET /solicitudes-consultas`, `POST /programas`, `POST /modulos`, `GET /usuarios` y Express `POST /sedes` | ✔ 401 |
| F5 | Usuario ajeno: leer solicitud / reasignar docente / asignar recurso | ✔ 403 (los tres) |
| F6 | Estudiante no puede marcar su solicitud `EN_PROCESO` ni `RESUELTA` | ✔ 403 (ambos) |
| F7 | Token con firma alterada → 401 en FastAPI y Express | ✔ 401 |
| F8 | Token expirado → 401 en FastAPI y Express | ✔ 401 |
| F9 | Usuario desactivado no puede iniciar sesión | ✔ 401 |
| F10 | El Bearer se reenvía a Express al asignar recurso (docente asignado) | ✔ 200 con `ubicacion` |

## Suite Jest de Express (MySQL local)

`infraestructura-service` (MySQL 3307, bases `*_test`):

| Comando | Resultado |
|---|---|
| `npm test` (`jest --runInBand --forceExit`) | ✔ 8 suites / 46 tests |
| `npx jest --forceExit` (sin `--runInBand`, 8 workers) | ✔ 8 suites / 46 tests |

Bases creadas: `sistema_consultas_infra_test` y `sistema_consultas_infra_w1..w8_test` (todas terminan en `_test`). El arranque de pruebas aborta si el nombre no termina en `_test`, así que se respetó el sufijo.

## Paso H — Bugs

- Las sondas de seguridad no encontraron fallos de autorización/autenticación.
- Suite FastAPI: `python -m pytest -q` → **76 passed** (verificación previa).
- Observación (no corregida, comportamiento preexistente): `GET /notificaciones` y `GET /notificaciones/no-leidas/count` solo devuelven notificaciones de tipo `COMENTARIO`.

## Pendientes que dependen del usuario

1. **Despliegue**: no se desplegó nada ni se hizo push.
2. Los datos de Neon son de prueba; el esquema se recrea desde cero con `init_db` (semillas idempotentes).

## Cómo reproducir

```powershell
# Express (infraestructura-service, base *_verif)
& npm.cmd run db:init
& npm.cmd run start            # puerto 3001

# FastAPI (backend) contra PostgreSQL de verificación
$env:DB_URL=$env:DB_URL_VERIF                                   # host con <HOST_NEON_VERIFICACION>*
$env:JWT_SECRET=(<JWT_SECRET de infraestructura-service/.env>)  # mismo valor que Express; no imprimir
$env:ADMIN_CORREO='admin@test.com'; $env:ADMIN_PASSWORD='<clave>'; $env:ADMIN_IDENTIFICACION='9000000000'
$env:INFRA_SERVICE_URL='http://127.0.0.1:3001'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080     # desde backend/

# Verificación de esquema y comportamiento PostgreSQL
$env:DB_URL=$env:DB_URL_VERIF; python scripts/verificar_esquema.py

# Pruebas
python scripts/e2e.py full
python scripts/e2e.py caido      # con Express detenido
python scripts/seguridad.py
python scripts/infra_estructuras.py

# Suite Jest de Express (MySQL local, bases *_test)
& npm.cmd test                   # con --runInBand
& npx.cmd jest --forceExit       # sin --runInBand
```
