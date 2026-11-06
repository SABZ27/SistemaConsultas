# Scripts SQL para entregar a un compañero

Cinco archivos, dos motores independientes. **No contienen secretos,
contraseñas, correos personales ni datos reales**, y no se ha ejecutado nada
contra Neon ni contra Aiven.

## Orden de ejecución

| Motor | Orden | Archivos |
|---|---|---|
| PostgreSQL (dominio de negocio, FastAPI) | 1 → 2 | `01_postgres_schema.sql`, `02_postgres_seed.sql` |
| MySQL (servicios externos, Express) | 3 → 4 | `03_mysql_schema.sql`, `04_mysql_seed.sql` |

Cada par va sobre una base vacía. Los dos pares son independientes entre sí:
se pueden ejecutar en cualquier orden relativo, pero dentro de cada par el
esquema va antes que la semilla.

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

## Sobre `01_postgres_schema.sql` (ajuste del Bloque E)

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

## Sobre `02_postgres_seed.sql` (ajuste del Bloque E)

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

**No hay ningún usuario administrador en estos scripts.** Se crea
automáticamente al arrancar el backend, y solo si están las tres variables de
entorno:

- `ADMIN_CORREO`
- `ADMIN_PASSWORD`
- `ADMIN_IDENTIFICACION`

Si falta alguna, no se crea el administrador y se registra una advertencia en
el log (sin imprimir los valores). Aquí solo se documentan los **nombres** de
las variables; no se incluyen valores, contraseñas ni correos.

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
| PostgreSQL | **No se pudo validar en una base vacía**: no hay servidor local en `127.0.0.1:5432` ni cliente `psql`/`pg_isready` en el equipo, y está prohibido conectarse a Neon. Verificación **estática** del SQL generado: **19** `CREATE TABLE`, **19** `CREATE TRIGGER`, **16** índices parciales `WHERE estado`, **24** `FOREIGN KEY`. |
| MySQL | El puerto local `127.0.0.1:3307` responde (es el que usa jest), pero **la autenticación con parámetros explícitos falló** (`ER_ACCESS_DENIED_ERROR`). Siguiendo la instrucción, **no se intentaron credenciales de archivos `.env`** y se mantuvo la verificación **estática**: **4** `CREATE TABLE` en `03`. No se creó ni se dejó ninguna base: el intento de base temporal `docs_sql_e_test` se canceló antes de crearse y, de haberse creado, el script la elimina en `finally`. Nunca se tocó Aiven. |

Verificación estática adicional: `02` tiene 5 bloques `INSERT` y **ninguno**
sobre `usuarios`; no hay contraseñas ni correos personales en ningún archivo.

**Nada de esto está desplegado ni probado en producción**: son scripts de
entrega para un compañero, generados y revisados localmente.
