# Cómo crear una consulta

## Endpoint y quién puede hacerlo

`POST /solicitudes-consultas` devuelve **201**. Solo un usuario con rol
**ESTUDIANTE** puede crearla: si el rol no es ese, el servicio responde 400
`El usuario indicado no tiene el rol ESTUDIANTE.`. El usuario autenticado
queda como `estudiante_id` de la solicitud.

## Campos obligatorios del cuerpo

`RegistroSolicitudConsultaRequest` (`extra="ignore"`):

| Campo | Tipo / regla |
|---|---|
| `prioridad` | `ALTA`, `MEDIA` o `BAJA` (enum `PrioridadSolicitud`) |
| `asunto` | texto de 1 a 100 caracteres |
| `descripcion` | texto, mínimo 1 carácter |
| `fechaConsulta` | fecha `YYYY-MM-DD` |
| `horaConsulta` | hora `HH:MM` |
| `docenteId` | entero, id del docente |
| `moduloId` | entero, id de la asignatura (`modulos`) |

El estado inicial es **`PENDIENTE`**. El número de consulta se genera como
`SC-<año>-<max_id+1 con 6 dígitos>`, por ejemplo `SC-2026-000123`, es único y
se reintenta hasta **5** veces si choca con otro.

## Validaciones, en este orden

1. El usuario tiene rol `ESTUDIANTE`.
2. El docente existe, está activo y tiene rol `DOCENTE`.
3. La asignatura (`modulo`) existe y está activa.
4. **Periodo académico vigente**: la fecha debe caer dentro de un periodo con
   `estado = true` (`fecha_inicio <= fecha <= fecha_fin`); si no, 400
   `La fecha de la consulta no corresponde a un periodo académico vigente.`
5. **Festivo (fail-closed)**: se llama al servicio externo **antes** que a la
   disponibilidad. Ver `07-festivos-y-fechas.md`.
6. **Docente asignado a la asignatura**: debe existir una relación activa en
   `docentes_modulos` para ese docente y ese módulo; si no, 400.
7. **Disponibilidad del docente**: el día de la semana de la fecha
   (`1 = Lunes` ... `7 = Domingo`) debe tener un tramo activo cuya
   `hora_inicio` y `hora_fin` contengan la `horaConsulta`.
8. La fecha no puede ser **anterior a hoy**: 400
   `La fecha de la consulta no puede ser anterior a la fecha actual.`

Si la validación de festivos devuelve que la fecha es festiva, la operación se
rechaza con **400** y el mensaje exacto
`La fecha seleccionada es festivo: <nombre>`. Si el servicio externo no
responde, se rechaza con **503** (fail-closed): no se crea la consulta sin
haber validado la fecha.

Tras guardar se generan una notificación `NUEVA_SOLICITUD` hacia el docente,
un evento `CREACION` y un correo (en segundo plano, tras el commit).

## Reprogramar una consulta

`PUT /solicitudes-consultas/{id}` actualiza `prioridad`, `asunto`,
`descripcion`, `fecha_consulta`, `hora_consulta` y `modulo`.

- No se permite una fecha anterior a hoy.
- Si **cambia la fecha**, se **revalida el festivo** (fail-closed 503).
- Si cambia la **fecha o la hora**, el `motivo` no vacío es obligatorio
  (400 `Debe indicar un motivo cuando se modifica la fecha o la hora de la
  consulta.`).
- Si hubo cambio de agenda se notifica `CAMBIO_AGENDAMIENTO` y se registra el
  evento correspondiente.
- **No revalida** periodo académico vigente, la relación docente-módulo ni la
  disponibilidad del docente.

## Formatos y zona horaria

La fecha se serializa como `%Y-%m-%d` y la hora como `%H:%M`. Los campos son
`DATE` y `TIME WITHOUT TIME ZONE`: se comparan con la **hora local del
servidor** (`date.today()`, `datetime.now()`), sin conversión de zona horaria.
