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
   `Base.metadata.create_all()`.
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

Ver [`LEEME.md`](LEEME.md): `01 → 02 → 05` para PostgreSQL y
`03 → 04 → 06` para MySQL. Los pares son independientes entre sí.

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

Los correos son de dominio de ejemplo (`@ejemplo.edu.co`); no hay correos
personales ni datos reales.

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
- **Datos en español de Colombia:** nombres, 20 programas académicos, 20
  asignaturas, 20 sedes/zonas/recursos, asuntos, comentarios y calificaciones
  creíbles.
- **MySQL, bitácoras y correos:** no se pudieron generar ejecutando el flujo
  real en local (no hay proveedor Nager.Date/Brevo ni SMTP locales; las
  pruebas simulan las respuestas). Por tanto `consultas_servicio_externo` (20)
  y `correos_enviados` (20) son filas **sintéticas marcadas explícitamente**
  con el prefijo `[DEMO]` en `detalle` / `respuesta_proveedor`, con
  `exito = 0`, `codigo_http = NULL` y `estado_envio = FALLIDO`. **Nunca se
  presentan como llamadas ni envíos reales.** Los `festivos` sí son reales
  (2026 y 2027) y `servicios_externos` contiene los 2 proveedores reales
  más 8 filas de demostración inactivas (`estado = 0`) y marcadas.

## Validación realizada

| Motor | Resultado |
|---|---|
| PostgreSQL | Sin servidor local en `5432`; no se conectó a Neon. `05` se validó sobre **SQLite local** con el mismo esquema (`Base.metadata.create_all`), las semillas de `02` y `PRAGMA foreign_keys=ON`: 19 tablas, FK sin violaciones, 20 filas en cada tabla principal y ≥10 en cada secundaria. |
| MySQL | `06` se aplicó **dos veces** sobre la base local de pruebas `127.0.0.1:3307` mediante el arnés de jest: 38 festivos reales, 10 servicios, 20 bitácoras y 20 correos; la segunda ejecución no duplicó. Nunca se tocó Aiven. |

**Nada de esto se ha ejecutado en Neon ni en Aiven.**
