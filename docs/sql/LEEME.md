# Scripts SQL para entregar a un compañero

Ocho scripts `.sql` (`01`–`08`) y dos documentos (`SEMBRAR_DEMO.md` y este
`LEEME.md`). Dos motores independientes. **No contienen secretos ni correos
personales**; los datos son de demostración salvo los festivos colombianos
reales y los catálogos base. `07` y `08` son **solo `SELECT`**. No se ha
ejecutado nada contra Neon ni contra Aiven.

## Orden de ejecución de TODOS los scripts

| Paso | Motor | Archivo | Contenido |
|---|---|---|---|
| 1 | PostgreSQL | `01_postgres_schema.sql` | DDL de las 19 tablas, FK, únicos parciales, función y triggers |
| 2 | PostgreSQL | `02_postgres_seed.sql` | Semillas base: roles, `modulos_sistema`, `modulos_x_rol`, tipos de documento, periodo |
| 3 | MySQL | `03_mysql_schema.sql` | DDL de las 4 tablas de servicios externos |
| 4 | MySQL | `04_mysql_seed.sql` | 2 proveedores reales (Nager.Date, Brevo) |
| 5 | PostgreSQL | `05_datos_demo_postgres.sql` | Datos de demostración (20 principales / ≥10 secundarias) |
| 6 | MySQL | `06_datos_demo_mysql.sql` | Festivos reales 2026–2027 y filas demo marcadas `[DEMO]` |
| 7 | PostgreSQL | `07_verificar_demo.sql` | **Solo `SELECT`**: conteos, mínimos, FK huérfanas, calificaciones y domingos |
| 8 | MySQL | `08_verificar_demo_mysql.sql` | **Solo `SELECT`**: conteos, mínimos, huérfanos y coherencia `[DEMO]` |

Reglas del orden:

- **Dentro de cada motor el esquema va antes que las semillas y los datos**:
  `01 → 02 → 05 → 07` y `03 → 04 → 06 → 08`. `07`/`08` van al final, cuando
  ya existe la demo que verifican.
- Los pares de motores son independientes entre sí: se pueden ejecutar en
  cualquier orden relativo.
- `05` y `06` son **idempotentes** (`ON CONFLICT DO NOTHING` / `INSERT IGNORE`
  e IDs en rango alto), así que se pueden repetir sin duplicar filas.
- `07` y `08` **no modifican nada**: ni DDL ni DML, solo consultas. Se pueden
  ejecutar tantas veces como quiera.
- Para la siembra **local** existe el comando idempotente
  `python scripts/sembrar_demo.py`, documentado en
  [`SEMBRAR_DEMO.md`](SEMBRAR_DEMO.md). Los `.sql` de la nube los ejecuta el
  responsable del proyecto (paso pendiente).

## Versiones asumidas

- **PostgreSQL 15 o superior.** El repositorio no fija una versión: usa
  `SQLAlchemy >= 2.0.36` con `psycopg[binary] >= 3.2` sobre Neon, y no se ha
  conectado a Neon para consultar la versión exacta (está prohibido en este
  trabajo). El DDL usa `CREATE TABLE IF NOT EXISTS`,
  `CREATE ... INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`,
  `DROP TRIGGER IF EXISTS`, índices parciales `WHERE estado` y
  `EXECUTE FUNCTION`, disponibles en PostgreSQL 15+.
- **MySQL 8.0 / InnoDB / utf8mb4**, según la cabecera del SQL original de
  `infraestructura-service/sql/schema.sql`. El servicio Express usa `mysql2`
  sobre Node 24.

## Sobre `01_postgres_schema.sql` (Bloque E)

- **Se generó compilando los modelos SQLAlchemy** (`backend/app/models`) con el
  dialecto de PostgreSQL, **sin conectarse a ninguna base de datos**.
- **La fuente de verdad sigue siendo `init_db()`**
  (`backend/app/db/session.py`): `Base.metadata.create_all()` y
  `_crear_triggers_actualizado_postgres()`. Este archivo es una **instantánea**,
  **no una migración incremental**: no sustituye a las migraciones 001–005 ni
  a cambios futuros de esquema. Si los modelos cambian, hay que regenerarlo.
- Incluye llaves foráneas, `CHECK`, únicos parciales (`WHERE estado`), la
  función `set_actualizado()` y **un trigger por tabla**, en el mismo orden
  (`Base.metadata.sorted_tables`) que usa `init_db()`.
- **Cierra con una consulta de comprobación comentada**: conteo de tablas del
  esquema `public`, que debe devolver **19**.

## Sobre `02_postgres_seed.sql` (Bloque E)

Replica **todo lo que inserta `ejecutar_seeds()`** al arrancar
(`backend/app/db/seeds.py`) sobre la base vacía:

| Bloque | Contenido | Filas |
|---|---|---|
| `roles` | `ADMINISTRADOR`, `DOCENTE`, `ESTUDIANTE` | 3 |
| `modulos_sistema` | nombre, descripción, ruta, icono | 15 |
| `modulos_x_rol` | matriz `MATRIZ_MODULOS_X_ROL`, resuelta por nombre | 24 |
| `tipos_documento` | CC, TI, CE, PAS | 4 |
| `periodos_academicos` | periodo vigente | 1 |

Los **4 tipos de documento y el periodo académico vigente se incluyeron en
este bloque** a petición expresa; en el plan inicial solo se contemplaban
roles y módulos. El periodo usa el nombre `2026-1` y el rango
`2026-01-01` → `2026-12-31`, que cubre el semestre actual (2026-2,
julio–diciembre), y lleva **un comentario que indica que las fechas y el
nombre deben ajustarse al calendario académico real** antes de ejecutarlo en
un entorno definitivo. El `LEEME` lo recuerda aquí también:

> **El periodo `2026-1` del seed (1 de enero a 31 de diciembre de 2026) debe
> ajustarse al calendario real.** Es el rango anual que genera
> `ejecutar_seeds()`, no una fecha académica oficial; antes de usar estos
> scripts hay que sustituir el nombre, `fecha_inicio` y `fecha_fin` por los
> valores del calendario institucional.

Todos los bloques son idempotentes (`INSERT ... SELECT ... WHERE NOT EXISTS`),
respetan la comprobación de solape de periodos y **no insertan el usuario
administrador**.

## Administrador inicial

**No hay ningún usuario administrador en `01`–`04`.** Se crea
automáticamente al arrancar el backend, y solo si están las tres variables de
entorno:

- `ADMIN_CORREO`
- `ADMIN_PASSWORD`
- `ADMIN_IDENTIFICACION`

Si falta alguna, no se crea el administrador y se registra una advertencia en
el log (sin imprimir los valores). Aquí solo se documentan los **nombres** de
las variables; no se incluyen valores, contraseñas ni correos.

## Sobre `05_datos_demo_postgres.sql` (Bloque B)

Datos de demostración en español de Colombia para las 19 tablas: 20 registros
en cada tabla principal y 10 o más en cada secundaria (contando las semillas
base). Incluye los 3 roles canónicos de forma idempotente, 20 usuarios demo
(12 estudiantes, 6 docentes, 2 administradores) con correos en el subdominio
reservado `@demo.ejemplo.edu.co` y **solo el hash bcrypt** de
`DEMO_PASSWORD`, 20 programas, 20 asignaturas, 20 sedes/zonas/recursos, 20
solicitudes con `numero_consulta` `SC-2026-9000xx` en fechas que no son
domingo ni festivo colombiano de 2026/2027, 10 calificaciones **solo sobre
consultas `RESUELTAS`**, 20 comentarios (15 del docente asignado, para que se
vea `retroalimentacionDocente`), 20 notificaciones y 20 eventos coherentes
con el estado, y 10 tokens de recuperación con hash. Los nombres de relleno
de los 7 roles de catálogo, los 10 `modulos_sistema` y los 6
`tipos_documento` son cargos y denominaciones realistas en español de
Colombia; los 3 roles canónicos no se tocan y no se amplía ningún permiso
(la matriz demo enlaza solo roles de catálogo inactivos). Detalle completo en
[`SEMBRAR_DEMO.md`](SEMBRAR_DEMO.md).

**Auditado para PostgreSQL real**: va dentro de `BEGIN` / `COMMIT`; usa
`ON CONFLICT DO NOTHING` sin objetivo (el único que cubre a la vez la PK por
IDs explícitos y los 16 índices únicos parciales `WHERE estado` de `01`);
booleanos `TRUE`/`FALSE` y literales de fecha/hora válidos en PostgreSQL, sin
sintaxis exclusiva de SQLite; y al final resincroniza **las 19 secuencias
`SERIAL`** con `setval(pg_get_serial_sequence(tabla, 'id'), ...)`. Ejecutarlo
dos veces no duplica filas. Las colisiones con los datos de prueba de Neon
(1 docente, 1 estudiante, 1 programa, 1 módulo) se evitan por construcción:
correos en subdominio reservado, identificaciones con prefijo `9` y nombres
de programas/asignaturas con prefijo `[DEMO]`. No se consultó Neon.

## Sobre `06_datos_demo_mysql.sql` (Bloque B)

38 festivos **reales** de Colombia 2026 y 2027 (19 por año, con la corrección
Ley Emiliani), los 2 proveedores reales más 8 servicios de demostración
inactivos y marcados con **nombres realistas en español de Colombia** (no
`[DEMO] Proveedor N`), y 20 `consultas_servicio_externo` + 20
`correos_enviados` **sintéticos marcados explícitamente con `[DEMO]`** en
`detalle` / `respuesta_proveedor`, con `exito = 0`, `codigo_http = NULL` y
`estado_envio = FALLIDO`. No se generaron ejecutando el flujo real en local
(no hay proveedor ni SMTP locales; las pruebas simulan las respuestas) y
**nunca se presentan como llamadas ni envíos reales**. Decisión documentada en
[`SEMBRAR_DEMO.md`](SEMBRAR_DEMO.md).

## Sobre `07_verificar_demo.sql` (solo `SELECT`, PostgreSQL)

Verifica la demo del backend sin modificar nada:

- conteo de **las 19 tablas** con columna `cumple` contra el mínimo
  (**20** para las 12 tablas principales, **10** para las 7 secundarias);
- las **24 FK** de `01` (filas huérfanas, todas deben dar 0);
- que las `calificaciones_consulta` estén **solo sobre consultas `RESUELTAS`**;
- que **ninguna solicitud esté agendada en domingo**
  (`EXTRACT(DOW FROM fecha_consulta) = 0`, exclusivo de PostgreSQL).

## Sobre `08_verificar_demo_mysql.sql` (solo `SELECT`, MySQL)

Verifica la demo del servicio externo sin modificar nada:

- conteo de **las 4 tablas** con columna `cumple` (**20** para `festivos`,
  `consultas_servicio_externo` y `correos_enviados`; **10** para
  `servicios_externos`);
- las **5 FK** de `03` (huérfanos, todos deben dar 0);
- coherencia `[DEMO]`: bitácoras con `exito = 0` y correos con
  `estado_envio = FALLIDO`, ambos marcados con el prefijo `[DEMO]`.

## `03` y `04` (MySQL)

Son **copias byte a byte, sin modificar una sola línea**, de:

- `infraestructura-service/sql/schema.sql` → `03_mysql_schema.sql` (4 tablas:
  `servicios_externos`, `consultas_servicio_externo`, `festivos`,
  `correos_enviados`).
- `infraestructura-service/sql/seed-servicios.sql` → `04_mysql_seed.sql`
  (2 proveedores: Nager.Date y Brevo).

Se verificó con SHA-256 que origen y copia son idénticos.

## Validación realizada (y lo que no se pudo probar)

| Motor | Resultado |
|---|---|
| PostgreSQL | **No hay servidor local en `127.0.0.1:5432`** ni cliente `psql`; está prohibido conectarse a Neon. `01` se verificó de forma estática (19 `CREATE TABLE`, 19 triggers, 16 índices parciales, 24 FK). `05` se auditó de forma estática para PostgreSQL real (`BEGIN`/`COMMIT`, 19 `setval`, `ON CONFLICT` sin objetivo, sin sintaxis SQLite) y se aplicó **dos veces** sobre **SQLite local** (`Base.metadata.create_all` + semillas de `02` + `PRAGMA foreign_keys=ON`), omitiendo solo `BEGIN`/`COMMIT`/`setval`: 19 tablas, 0 FK huérfanas, 20 filas por principal y ≥10 por secundaria, sin duplicar. `07` **no se puede ejecutar tal cual en SQLite** por `EXTRACT(DOW FROM ...)`; se validó una **adaptación equivalente** (`strftime('%w', ...)`) sobre la misma base: las 19 tablas `CUMPLE`, las 24 FK con 0 huérfanas, 0 calificaciones fuera de `RESUELTAS` y 0 solicitudes en domingo. |
| MySQL | El puerto local `127.0.0.1:3307` responde. En el Bloque E la autenticación con parámetros explícitos falló (`ER_ACCESS_DENIED_ERROR`) y **no se intentaron credenciales de `.env`**, por lo que `03`/`04` se verificaron de forma estática. `06` y `08` **sí se ejecutaron** sobre la base local de pruebas mediante el arnés de jest: `06` aplicado **dos veces** (38 festivos, 10 servicios, 20 bitácoras y 20 correos, sin duplicar) y `08` con sus 3 `SELECT` (4 tablas `CUMPLE`, 5 FK con 0 huérfanos, coherencia `[DEMO]`). Nunca se tocó Aiven. |

Verificación adicional: `02` tiene 5 bloques `INSERT` y ninguno sobre
`usuarios`; `05` contiene únicamente el hash bcrypt (nunca la contraseña en
claro); no hay correos personales en ningún archivo.

**Nada de esto está desplegado ni probado en producción**: son scripts de
entrega para un compañero, generados y revisados localmente. El responsable
del proyecto ejecuta los `.sql` en Neon y en Aiven y realiza el push.

## Supuestos y puntos no verificados

- **(a)** La API usa `routes → services → repositories → schemas`.
- **(b)** **«CRUD en todos los roles» se interpretó como CRUD sobre las
  entidades propias de cada rol**, sin ampliar permisos de escritura de ningún
  rol (decisión documentada en `docs/decisiones.md`).
- **(c)** **La calificación la crea el estudiante dueño de la consulta
  resuelta**; no se invirtió esa regla de negocio.
- **(d)** Las filas de `consultas_servicio_externo` y `correos_enviados` son
  datos `[DEMO]`, con `exito = 0` y `FALLIDO`, nunca llamadas reales.
- **(e)** Los festivos de 2027 se calcularon con las reglas de Ley Emiliani y
  el cómputo de Pascua, tomando como referencia el fixture real de 2026 de
  Nager.Date. No se consultó la API en la nube.
