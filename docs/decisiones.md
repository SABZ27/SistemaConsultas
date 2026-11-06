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
Desde el Bloque A la validación de festivos es **fail-closed**: si el servicio externo no responde (fallo de red, timeout o indisponibilidad), la creación/reprogramación se rechaza con **503** en lugar de omitir la validación. Los festivos ya guardados en caché se resuelven localmente y no dependen del proveedor; la trazabilidad de las llamadas queda registrada en MySQL (`consultas_servicio_externo`, `festivos`).

## IP del cliente detrás de proxies (TRUSTED_PROXY_HOPS)

La IP que se usa como clave de los limitadores se toma de `X-Forwarded-For`
en la posición `-(TRUSTED_PROXY_HOPS + 1)` contando desde la derecha: se
descartan las `TRUSTED_PROXY_HOPS` últimas entradas (los proxies) y se ignoran
las de la izquierda, que el cliente puede falsificar. Si el encabezado falta,
tiene menos de `hops + 1` entradas o **cualquiera** de sus entradas está vacía,
malformada o no es una IP válida, se usa `request.client.host`.

### Medición de TRUSTED_PROXY_HOPS en Render (N-1)

El valor por defecto es **`TRUSTED_PROXY_HOPS=0`** (`config.py` y
`.env.example`), pensado para local y pruebas, donde no hay proxies. Si no se
configura en Render, se toma la última entrada de `X-Forwarded-For` (la del
edge), compartida por todos los clientes: quedan agrupados bajo una sola clave
y los límites por IP se vuelven globales, con riesgo de `429` masivo. El valor
real no se deduce del ejemplo «cliente, edge» ni de la documentación del
proveedor; hay que medirlo en el propio despliegue:

1. En **producción**, activar `DIAGNOSTICO_IP=true` durante unos minutos y
   volver a `false` en cuanto se haya observado el patrón. El diagnóstico solo
   registra el número de entradas de `X-Forwarded-For` y si existe
   `True-Client-IP` (conteos y booleanos); **nunca registra direcciones IP**.
2. Observar en el log el valor estable de `x_forwarded_for_entradas` = **N**
   para el tráfico normal durante esa ventana.
3. Con la convención de `X-Forwarded-For` (el cliente es la primera entrada y
   cada proxy añade la suya al final), el valor es **N - 1**: se descartan las
   N-1 entradas añadidas por los proxies y se conserva la del cliente.
4. Repetir la medición tras cualquier cambio de topología, CDN, región o plan:
   el valor puede cambiar.
5. Fijar `TRUSTED_PROXY_HOPS` en el panel de Render con el resultado y
   confirmar que `DIAGNOSTICO_IP` quedó en `false`.

El diagnóstico solo da conteos: no muestra la cadena y, por tanto, no confirma
por sí solo que la primera entrada sea el cliente real. Esa comprobación
requiere una observación controlada adicional, sin volcar IPs en los logs.

### Riesgo de agrupar IPs

Si `TRUSTED_PROXY_HOPS` queda por debajo del número real de proxies, se toma
como cliente la última entrada (la del edge), compartida por muchos clientes:
**todos quedan agrupados bajo una sola clave** y los límites por IP se vuelven
globales, con riesgo de `429` masivo. Si queda por encima, se cae a
`request.client.host` (también compartido) o se selecciona una entrada
intermedia. Por eso el límite por IP del login se mantiene alto (**100 fallos /
15 min**) mientras siguen activos los límites por pareja correo+IP (5) y por
correo (15), que no dependen de una única IP compartida.

Esta resolución por saltos asume que el servicio solo recibe tráfico a través
de los proxies de Render; **no valida la confianza de las entradas**. Si esa
condición operativa cambiara (acceso directo o un proxy que no limpie el
`X-Forwarded-For` entrante), la decisión debe revisarse.
