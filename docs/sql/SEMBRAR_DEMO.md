# Siembra de datos de demostración (solo local)

Los datos de demostración viven en `05_datos_demo_postgres.sql` (PostgreSQL /
Neon) y `06_datos_demo_mysql.sql` (MySQL / Aiven). **El responsable del
proyecto ejecuta los `.sql` en Neon y en Aiven**; aquí solo se documenta la
siembra **local**.

## Comando idempotente

```bash
python scripts/sembrar_demo.py
```

Es idempotente: los `.sql` usan `ON CONFLICT DO NOTHING` (PostgreSQL/SQLite) e
`INSERT IGNORE` (MySQL), con IDs fijos en rango alto. Ejecutarlo dos veces no
duplica filas. El script:

1. Aplica `05_datos_demo_postgres.sql` sobre `DEMO_DB_URL` (por defecto un
   SQLite local en el directorio temporal); si es SQLite, crea el esquema con
   `Base.metadata.create_all()`. `05` está auditado para **PostgreSQL real**
   (`BEGIN`/`COMMIT` y 19 `setval(pg_get_serial_sequence(...))`): en un motor
   que no sea PostgreSQL el script omite esas sentencias, porque SQLAlchemy ya
   gestiona la transacción con `motor.begin()` y SQLite no tiene secuencias
   `SERIAL`. En Neon el `.sql` se ejecuta completo tal cual.
2. Si se definen `DEMO_MYSQL_USER` y `DEMO_MYSQL_DATABASE` y existe el cliente
   `mysql`, aplica `06_datos_demo_mysql.sql`. Si no, imprime el comando
   equivalente para ejecutarlo a mano.

Variables de entorno opcionales (el script **no lee ningún `.env`**, no
imprime contraseñas ni cadenas de conexión):

| Variable | Uso |
|---|---|
| `DEMO_DB_URL` | URL SQLAlchemy del backend; por defecto SQLite local temporal |
| `DEMO_MYSQL_HOST` / `DEMO_MYSQL_PORT` | `127.0.0.1` / `3307` por defecto |
| `DEMO_MYSQL_USER` / `DEMO_MYSQL_PASSWORD` | credenciales **locales** |
| `DEMO_MYSQL_DATABASE` | base local, nombre terminado en `_test` |

Comando MySQL equivalente (también idempotente):

```bash
mysql -h 127.0.0.1 -P 3307 -u <usuario> -p <base_test> < docs/sql/06_datos_demo_mysql.sql
```

## Orden completo de scripts

Ver [`LEEME.md`](LEEME.md): `01 → 02 → 05 → 07` para PostgreSQL y
`03 → 04 → 06 → 08` para MySQL. Los pares son independientes entre sí.
`07` y `08` son scripts de verificación **solo `SELECT`**, se ejecutan al
final y no modifican nada.

## Contraseña de los usuarios demo

`05` contiene **solo el hash bcrypt** de la contraseña, nunca la contraseña en
claro. El hash se generó a partir de `DEMO_PASSWORD` (debe cumplir la política
de `app/core/password_policy.py`: 10–72 caracteres, mayúscula, minúscula,
número, símbolo, sin datos personales). Si `DEMO_PASSWORD` no estaba definida
al generar, se usó el valor de demostración por defecto **`Taller#Demo2026`**
(no es un secreto real; es la credencial de las cuentas demo). Para usar otra
contraseña, define `DEMO_PASSWORD` y vuelve a generar el SQL con el
procedimiento de este bloque; el hash cambiará y las cuentas demo usarán la
nueva contraseña.

Los correos usan el subdominio reservado de demostración
`@demo.ejemplo.edu.co`; no hay correos personales ni datos reales.

## Auditoría de `05` para PostgreSQL real

- **Transacción atómica:** `BEGIN;` … `COMMIT;`. Si algo falla, no queda
  siembra parcial.
- **Secuencias:** como se insertan IDs explícitos (1000–2809), al final se
  resincronizan **las 19 secuencias `SERIAL`** con
  `SELECT setval(pg_get_serial_sequence('<tabla>', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)`
  para que los siguientes `INSERT` de la API no choquen con la PK.
- **`ON CONFLICT DO NOTHING` sin objetivo:** es el único que cubre a la vez la
  PK (IDs explícitos), los `UNIQUE` simples y los **16 índices únicos
  parciales `WHERE estado`** de `01`. Un objetivo explícito
  `ON CONFLICT (nombre) WHERE estado` no cubriría las filas inactivas ni los
  conflictos de PK y rompería la idempotencia en la segunda ejecución.
- **Sin sintaxis exclusiva de SQLite:** booleanos `TRUE`/`FALSE`, literales
  `'YYYY-MM-DD'`, `'HH:MM'` y `'YYYY-MM-DD HH:MM:SS'` (PostgreSQL los
  convierte implícitamente a `DATE`/`TIME`/`TIMESTAMP`), subconsultas
  escalares y `CURRENT_TIMESTAMP`.
- **Colisiones con los datos de prueba de Neon** (1 docente, 1 estudiante,
  1 programa, 1 módulo) evitadas por construcción: correos en subdominio
  reservado, identificaciones `9000000001`…`9000000020` y nombres de
  programas/asignaturas con prefijo `[DEMO]`. **No se consultó Neon.**
- **Idempotencia:** ejecutarlo dos veces no duplica filas y deja las 19
  secuencias en el mismo valor.

## Nombres de relleno

Los 7 roles de catálogo, los 10 `modulos_sistema`, los 6 `tipos_documento` y
los 8 servicios demo de MySQL dejaron de ser etiquetas genéricas: ahora son
cargos, módulos, documentos y servicios con nombres realistas en español de
Colombia. No se tocaron los 3 roles canónicos (`ADMINISTRADOR`, `DOCENTE`,
`ESTUDIANTE`) ni se amplió ningún permiso: la matriz `modulos_x_rol` demo
enlaza únicamente roles de catálogo inactivos con módulos de demostración.

## Decisiones tomadas en este bloque

- **Fechas de consulta:** 20 fechas de 2026, ninguna en domingo ni en festivo
  colombiano de 2026/2027 (lista real de 19 festivos por año, con la
  corrección Ley Emiliani aplicada). Todas caen dentro del periodo `2026-1`.
- **`numero_consulta`:** `SC-2026-900001` … `SC-2026-900020` (formato
  `SC-AAAA-NNNNNN`). El rango `9xxxxx` está reservado para la demostración y
  evita colisionar con la numeración de producción.
- **Índices únicos parciales de `usuarios`:** `correo` e `identificacion`
  únicos entre activos; los 20 usuarios usan valores distintos. Todas las FK
  se validaron con `PRAGMA foreign_key_check` sobre SQLite local.
- **Calificaciones:** 10, una por cada una de las 10 consultas `RESUELTAS`.
  Ninguna sobre `PENDIENTE`, `EN_PROCESO`, `CANCELADA` ni `RECHAZADA`.
- **Notificaciones y eventos:** coherentes con el estado de cada consulta
  (`NUEVA_SOLICITUD`/`CREACION` para pendientes, `CAMBIO_ESTADO` para
  atendidas y resueltas, `CANCELACION`/`RECHAZO` para las restantes).
- **Comentarios del docente:** 15 de las 20 consultas atendidas tienen un
  comentario activo escrito por el docente asignado, de modo que
  `retroalimentacionDocente` se ve en el detalle y en el listado.
- **Datos en español de Colombia:** nombres, 20 programas académicos y 20
  asignaturas creíbles (con prefijo `[DEMO]` para no colisionar con el programa
  y el módulo de prueba de Neon), 20 sedes/zonas/recursos, asuntos, comentarios
  y calificaciones creíbles.
- **MySQL, bitácoras y correos:** no se pudieron generar ejecutando el flujo
  real en local (no hay proveedor Nager.Date/Brevo ni SMTP locales; las
  pruebas simulan las respuestas). Por tanto `consultas_servicio_externo` (20)
  y `correos_enviados` (20) son filas **sintéticas marcadas explícitamente**
  con el prefijo `[DEMO]` en `detalle` / `respuesta_proveedor`, con
  `exito = 0`, `codigo_http = NULL` y `estado_envio = FALLIDO`. **Nunca se
  presentan como llamadas ni envíos reales.** Los `festivos` sí son reales
  (2026 y 2027) y `servicios_externos` contiene los 2 proveedores reales
  más 8 servicios de demostración inactivos (`estado = 0`), marcados con
  `[DEMO]` y con nombres realistas (ya no `[DEMO] Proveedor N`).

## Validación realizada

| Motor | Resultado |
|---|---|
| PostgreSQL | Sin servidor local en `5432`; no se conectó a Neon. Auditoría estática de `05` (`BEGIN`/`COMMIT`, 19 `setval`, `ON CONFLICT` sin objetivo, sin sintaxis SQLite) y aplicación **dos veces** sobre **SQLite local** con el mismo esquema (`Base.metadata.create_all`), las semillas de `02` y `PRAGMA foreign_keys=ON`, omitiendo solo `BEGIN`/`COMMIT`/`setval`: 19 tablas, FK sin violaciones, 20 filas en cada tabla principal y ≥10 en cada secundaria, sin duplicar. `07` no se puede ejecutar tal cual en SQLite (`EXTRACT(DOW FROM ...)`); se validó una **adaptación equivalente** con `strftime`: 19 tablas `CUMPLE`, 24 FK con 0 huérfanas, 0 calificaciones fuera de `RESUELTAS` y 0 domingos. |
| MySQL | `06` se aplicó **dos veces** y `08` se ejecutó con sus 3 `SELECT` sobre la base local de pruebas `127.0.0.1:3307` mediante el arnés de jest: 38 festivos reales, 10 servicios, 20 bitácoras y 20 correos; la segunda ejecución no duplicó y las 4 tablas, las 5 FK y la coherencia `[DEMO]` dieron `CUMPLE`. Nunca se tocó Aiven. |

**Nada de esto se ha ejecutado en Neon ni en Aiven.**
