# Decisiones de diseño

## Módulos vs módulos_sistema
Se mantiene separación conceptual: modulos_sistema define los módulos disponibles en la aplicación y modulos_x_rol controla permisos por rol. La lógica de autorización usa esta matriz.

## Borrado lógico y estado
Todas las entidades relevantes utilizan borrado lógico mediante columna estado (boolean/bit) en lugar de DELETE físico, permitiendo trazabilidad e integridad histórica.

## estado_consulta
Las solicitudes de consulta gestionan su estado a través del enum/valor estado_consulta, con transiciones controladas por reglas de negocio.

## JWT con rol y módulos
El token JWT incluye rol y modulos permitidos para el usuario, utilizado por middlewares/decoradores de autorización.

## Estructuras de sede BLOQUES/SALONES/PISOS
La infraestructura física se organiza jerárquicamente: Sede → Bloque/Zona → Recurso físico. Tipificación según reglas BLOQUES/SALONES/PISOS cuando aplica.

## Referencia con FK entre servicios
Tras la migración **005** (`backend/migrations/005_infraestructura_postgres.sql`), la infraestructura física vive en PostgreSQL (FastAPI). `solicitudes_consultas.recurso_fisico_id` tiene FK hacia `recursos_fisicos(id)` con `ON DELETE SET NULL`. En la migración se limpian las referencias heredadas de MySQL antes de crear la FK.

## Únicos parciales
Se utilizan índices únicos parciales (WHERE estado = true/1) para garantizar unicidad entre registros activos sin afectar históricos.

## Migración 004
La migración 004_tablas_nuevas.sql fue creada para implementar las cinco tablas nuevas de la Fase 5 (docentes_modulos, tipos_documento, calificaciones_consulta, periodos_academicos, disponibilidad_docente), añadir FK tipo_documento_id a usuarios, y establecer checks/índices únicos parciales. Esto es una desviación respecto al plan de backend original, el cual solo preveía las migraciones 001, 002 y 003; se justifica porque la Fase 5 requiere estas tablas para las validaciones de periodo/asignación/disponibilidad en solicitudes de consulta.

## Migraciones 001 a 003 (sin prueba contra bases reales)
Las migraciones 001_auditoria.sql, 002_roles_modulos.sql y 003_infraestructura.sql se mantuvieron en el repositorio como referencia (documentadas). Para esta verificación no se probaron contra bases reales (PostgreSQL/MySQL reales), tal como se solicitó: se omitió el Paso G a propósito. Para entornos reales deben aplicarse siguiendo el orden descrito, no como parte de este ejercicio de verificación.

## Servicios externos: Nager.Date y Brevo
Se utilizan **Nager.Date** para consultar días festivos por país (incluida la corrección de fechas móviles como **Ley Emiliani**: Ascensión y Corpus Christi, según el país/reglas aplicables) y **Brevo** para el envío de correos transaccionales. El microservicio Express centraliza estas llamadas, guarda la traza en MySQL (`consultas_servicio_externo`, `festivos`, `correos_enviados`) y expone `GET /festivos/validar` y `POST /correos`.

## Validación de festivos (fail-open)
Al crear o reprogramar una solicitud (`POST /solicitudes-consultas`, `PUT /solicitudes-consultas/{id}`), el backend valida la fecha contra el servicio de festivos **antes** de la validación de disponibilidad. Si la fecha es festiva, la operación se rechaza con **400** y el mensaje exacto `La fecha seleccionada es festivo: <nombre>`. Si el microservicio no está disponible o responde con error, la validación se omite (**fail-open**) y la solicitud se registra igualmente, dejando un aviso en el log con fecha, tipo de error y código HTTP **solo** si Express respondió 401/403 (sin nombres, correos ni identificadores). La validación depende del proveedor (Nager.Date/Express); ante indisponibilidad no se bloquea el flujo.

## Token interno rol SERVICIO para correos
El envío de correos es una operación de **servicio a servicio**. El backend firma un token JWT interno con rol **`SERVICIO`** (mismo `JWT_SECRET` en ambos servicios, vida corta de 5 minutos) y lo envía en `Authorization: Bearer`. Express exige ese rol en `POST /correos`: cualquier token de usuario autenticado recibe **403**. El token del usuario **no** se reenvía para el envío de correos. Los correos se programan con `BackgroundTasks` y se envían después del commit de la transacción.

## Limitación: dependencia del proveedor
La validación de festivos depende del servicio externo. En caso de fallo de red/timeout o indisponibilidad del proveedor, se aplica **fail-open** (no se bloquea la creación/reprogramación). La trazabilidad queda registrada en MySQL (`consultas_servicio_externo`, `festivos`).
