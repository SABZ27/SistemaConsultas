# Notificaciones y correos

## Tipos

`TipoNotificacion` (7 valores): `NUEVA_SOLICITUD`, `CAMBIO_ESTADO`,
`REASIGNACION`, `ASIGNACION_RECURSO`, `CAMBIO_AGENDAMIENTO`, `CANCELACION`,
`COMENTARIO`.

`TipoEvento` (8 valores): `CREACION`, `RECHAZO`, `CAMBIO_ESTADO`,
`CANCELACION`, `ASIGNACION_RECURSO`, `REASIGNACION_DOCENTE`, `COMENTARIO`,
`CAMBIO_AGENDAMIENTO`.

## Qué genera cada acción

| Acción | Tipo de notificación | Destinatario | ¿Correo? |
|---|---|---|---|
| Crear consulta (`POST /solicitudes-consultas`) | `NUEVA_SOLICITUD` | docente | Sí |
| Reprogramar (`PUT ...`) | `CAMBIO_AGENDAMIENTO` | contraparte | Sí |
| Cambio de estado (`PATCH .../estado`) | `CANCELACION` si `CANCELADA`, si no `CAMBIO_ESTADO` | contraparte | Sí |
| Asignar recurso (`PATCH .../recurso-fisico`) | `ASIGNACION_RECURSO` | estudiante | Sí |
| Reasignar docente (`PATCH .../docente`) | `REASIGNACION` | nuevo docente | Sí |
| Nuevo comentario (`POST /comentarios`) | `COMENTARIO` | contraparte | **No** |

Títulos de cambio de estado: `Solicitud aceptada` (`EN_PROCESO`),
`Solicitud rechazada`, `Consulta cancelada`, `Consulta resuelta`.

Toda notificación se persiste con `leida = false`. **Todos los tipos generan
un correo pendiente excepto `COMENTARIO`**.

## Endpoints de notificaciones

- `GET /notificaciones`: solo las del destinatario autenticado.
- `GET /notificaciones/no-leidas/count`.
- `PATCH /notificaciones/{id}/leer`: solo el destinatario.
- `DELETE /notificaciones/{id}`: baja lógica (`estado = false`), solo el
  destinatario.

## Envío de correos

- El backend **no envía correos directamente**: programa un `CorreoPendiente`
  con `BackgroundTasks` y lo despacha **después del commit**.
- El cliente llama a `POST {INFRA_SERVICE_URL}/correos` y espera **201**,
  **sin reintentos** para no duplicar envíos.
- El servicio Express usa **Brevo por API HTTP** (`POST .../smtp/email`,
  cabecera `api-key`), no SMTP. Si falta la clave del proveedor o el remitente,
  responde **503**; si falla el envío, **502**.
- `POST /correos` exige un **token interno de servicio** con rol `SERVICIO`
  (`crear_token_interno`, **5 minutos**, firmado con el mismo `JWT_SECRET`).
  Un token de usuario autenticado recibe **403**. El token del usuario **no se
  reenvía** para enviar correos.
- La traza queda en MySQL en `correos_enviados` (destinatario, asunto,
  `estado_envio` = `ENVIADO`/`FALLIDO`, `respuesta_proveedor`) y en
  `consultas_servicio_externo` (endpoint, código HTTP, éxito, duración).
  Se registra incluso cuando el envío falla.
- Si el envío falla, el backend solo escribe un aviso en el log y **no rompe
  el flujo** principal.

## Recuperación de contraseña

`POST /auth/forgot-password` da **la misma respuesta** exista o no el correo
(no revela si la cuenta existe), devuelve 200 y envía el correo **en segundo
plano**. El token se guarda **hasheado con SHA-256**, es de **un solo uso** y
expira a los **30 minutos**; `POST /auth/reset-password` valida token, uso,
expiración y la política de la nueva contraseña.
