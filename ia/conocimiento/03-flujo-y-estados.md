# Flujo de una consulta y sus estados

## El campo de estado

El estado de la solicitud vive en `solicitudes_consultas.estado_consulta`,
un `VARCHAR(50)` (no un tipo ENUM nativo de PostgreSQL). **No debe confundirse**
con `estado`, columna booleana de borrado lógico presente en todas las tablas.

Valores exactos del enum `EstadoSolicitud`:

`PENDIENTE`, `RECHAZADA`, `EN_PROCESO`, `RESUELTA`, `CANCELADA`.

El estado inicial de toda consulta creada es **`PENDIENTE`**.

## Transiciones permitidas

| Desde | Hacia permitido |
|---|---|
| `PENDIENTE` | `EN_PROCESO`, `RECHAZADA`, `CANCELADA` |
| `EN_PROCESO` | `RESUELTA`, `CANCELADA` |
| `RECHAZADA` | ninguno (terminal) |
| `CANCELADA` | ninguno (terminal) |
| `RESUELTA` | ninguno (terminal) |

Reglas de validación (`_validar_cambio_estado`):

- Pedir el **mismo estado** → 400 `La solicitud ya se encuentra en estado X.`
- Una transición no listada → 400 `No se puede cambiar el estado de X a Y`.
- Nunca se transiciona **hacia** `PENDIENTE`.

## Quién puede cambiar el estado

Endpoint: `PATCH /solicitudes-consultas/{id}/estado`, cuerpo
`{"estado": "...", "motivo": "..."}` (motivo opcional según el caso).

`_validar_actor_cambio_estado` se ejecuta antes de validar la transición:

- **Gestor** (permiso activo `GESTION_SOLICITUDES`; en la semilla solo
  `ADMINISTRADOR`): cualquier transición.
- **Docente asignado** a esa consulta: cualquier transición.
- **Estudiante dueño**: **solo `CANCELADA`**. Cualquier otro estado → 403
  `El estudiante solo puede cancelar su propia solicitud.`
- Cualquier otro usuario → 403.

El `motivo` no vacío es **obligatorio** para `RECHAZADA` y `CANCELADA`
(400 `Debe indicar un motivo para ...` si falta). No se exige para
`EN_PROCESO` ni `RESUELTA`.

Al cambiar el estado se registra una notificación y un evento de solicitud;
hay contenido de notificación definido para `EN_PROCESO`, `RECHAZADA`,
`CANCELADA` y `RESUELTA`.

## Borrado

`DELETE /solicitudes-consultas/{id}` es una **baja lógica** (pone
`estado = false`), solo para el gestor, y **no modifica** `estado_consulta`.

## Operaciones condicionadas por el estado

- **Comentarios y retroalimentación**: solo se pueden crear, y actualizar,
  cuando la consulta está en **`EN_PROCESO`**. Puede comentar cualquier
  participante (estudiante o docente).
- **Calificación**: solo se puede crear cuando la consulta está en
  **`RESUELTA`**, y solo por el estudiante dueño.
- **Asignar recurso físico**: solo en **`PENDIENTE`** o **`EN_PROCESO`**
  (`PATCH .../recurso-fisico`), por el docente asignado o un gestor.
- **Reasignar docente**: solo en **`PENDIENTE`** o **`EN_PROCESO`**
  (`PATCH .../docente`).

Por tanto, calificación y comentarios son mutuamente excluyentes por estado:
la primera exige `RESUELTA` y los segundos exigen `EN_PROCESO`.

## Eventos y notificaciones del flujo

Tipos de evento (`TipoEvento`): `CREACION`, `RECHAZO`, `CAMBIO_ESTADO`,
`CANCELACION`, `ASIGNACION_RECURSO`, `REASIGNACION_DOCENTE`, `COMENTARIO`,
`CAMBIO_AGENDAMIENTO`.

Tipos de notificación (`TipoNotificacion`): `NUEVA_SOLICITUD`,
`CAMBIO_ESTADO`, `REASIGNACION`, `ASIGNACION_RECURSO`,
`CAMBIO_AGENDAMIENTO`, `CANCELACION`, `COMENTARIO`.
