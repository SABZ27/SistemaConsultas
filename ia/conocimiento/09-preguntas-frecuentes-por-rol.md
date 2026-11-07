# Preguntas frecuentes por rol

Las respuestas se derivan de la documentación del sistema.

## Estudiante

**¿Puedo crear una consulta si soy docente o administrador?**
No. `POST /solicitudes-consultas` exige rol `ESTUDIANTE`; con otro rol responde
400 `El usuario indicado no tiene el rol ESTUDIANTE.`.
(Fuente: `04-crear-una-consulta.md`)

**¿En qué estado queda mi consulta recién creada?**
En `PENDIENTE`. Recibe un número con formato `SC-<año>-<6 dígitos>`.
(Fuente: `03-flujo-y-estados.md`, `04-crear-una-consulta.md`)

**¿Puedo cancelar mi consulta?**
Sí, pero el estudiante dueño **solo** puede pasarla a `CANCELADA`, y debe
indicar un `motivo` no vacío. Cualquier otro cambio de estado te da 403.
(Fuente: `03-flujo-y-estados.md`)

**¿Cuándo y cómo puedo calificar?**
Solo cuando la consulta esté `RESUELTA`, con `puntaje` de **1 a 5** y un
`comentario` opcional de hasta 500 caracteres. Una sola vez por consulta.
(Fuente: `05-calificacion.md`)

**¿Puedo corregir o borrar mi calificación?**
No: no existen endpoints `PUT`, `PATCH` ni `DELETE` de calificaciones; por API
es inmutable e indeleble.
(Fuente: `05-calificacion.md`)

**¿Puedo comentar?**
Sí, como participante, pero **solo mientras la consulta esté `EN_PROCESO`**.
(Fuente: `03-flujo-y-estados.md`, `05-calificacion.md`)

**¿Por qué me salió 400 con un nombre de festivo, o 503?**
400 `La fecha seleccionada es festivo: <nombre>` si elegiste un festivo; 503 si
el servicio de festivos no respondió (validación fail-closed).
(Fuente: `07-festivos-y-fechas.md`)

## Docente

**¿Puedo calificar una consulta que atendí?**
No. La calificación es exclusiva del estudiante dueño; si lo intentas recibes
403 `Solo el estudiante dueño puede calificar la consulta.`.
(Fuente: `05-calificacion.md`)

**¿Cómo dejo mi retroalimentación?**
Con un **comentario** en `/comentarios`, y solo en estado `EN_PROCESO`.
`retroalimentacionDocente` en la respuesta es tu comentario activo más reciente.
(Fuente: `05-calificacion.md`)

**¿Puedo cambiar el estado de una consulta?**
Sí: el docente asignado puede realizar cualquier transición permitida.
Recuerda que `RECHAZADA` y `CANCELADA` exigen `motivo`.
(Fuente: `03-flujo-y-estados.md`)

**¿Puedo asignar un recurso físico?**
Sí, el docente asignado o un gestor, y solo en `PENDIENTE` o `EN_PROCESO`.
El recurso debe existir y estar activo; la asignación **no** valida sede/zona,
ni disponibilidad horaria, ni doble reserva. Se guarda además una copia legible
`Sede · Zona · Recurso`.
(Fuente: `03-flujo-y-estados.md`, `04-crear-una-consulta.md`)

**¿Cómo registro mi disponibilidad?**
En `disponibilidad_docente`: `dia_semana` de 1 (Lunes) a 7 (Domingo), con
`hora_inicio` menor que `hora_fin`.
(Fuente: `07-festivos-y-fechas.md`)

**Me registré como docente: ¿ya recibo consultas?**
No por sí sola. Un administrador debe asignarte a una asignatura
(docentes-módulos) y tú debes tener disponibilidad.
(Fuente: `02-roles-y-modulos.md`)

## Administrador

**¿Qué módulo me da gestión global de solicitudes?**
`GESTION_SOLICITUDES`. Habilita listar todas, eliminar (baja lógica),
reasignar docente, asignar recurso, cambiar estado, ver calificaciones ajenas y
borrar comentarios. En la semilla solo lo tiene `ADMINISTRADOR`.
(Fuente: `02-roles-y-modulos.md`, `03-flujo-y-estados.md`)

**¿Puedo crear otro administrador con `/auth/register`?**
No: el registro público rechaza `ADMINISTRADOR` con 403. Solo permite
`ESTUDIANTE` y `DOCENTE`.
(Fuente: `02-roles-y-modulos.md`)

**¿Quién puede leer los catálogos?**
Cualquier usuario autenticado. Escribir o activar exige el módulo
correspondiente; `incluirInactivos=true` en sedes/zonas/recursos exige
`INFRAESTRUCTURA`.
(Fuente: `02-roles-y-modulos.md`)

**¿Qué hace `DELETE` sobre una consulta?**
Una baja lógica (`estado = false`), solo para el gestor. **No** cambia
`estado_consulta`.
(Fuente: `03-flujo-y-estados.md`)

## Generales

**¿Cuánto dura el token de sesión?**
30 minutos (`JWT_EXPIRATION_MINUTES`), firmado con HS256. El token interno de
servicio dura 5 minutos y el de recuperación 30 minutos.
(Fuente: `08-politica-de-contrasenas.md`)

**¿Qué pasa si fallo el login varias veces?**
Tras 5 fallos por pareja correo+IP (o 15 por correo, o 100 por IP) en 15
minutos llega un **429** con `Retry-After`; el bloqueo dura 15 minutos.
(Fuente: `08-politica-de-contrasenas.md`)

**¿Cuál es la diferencia entre `estado` y `estado_consulta`?**
`estado` es el booleano de borrado lógico de todas las tablas;
`estado_consulta` es la máquina de estados (`PENDIENTE`, `EN_PROCESO`,
`RESUELTA`, `RECHAZADA`, `CANCELADA`).
(Fuente: `03-flujo-y-estados.md`)

**¿Un "módulo" es una asignatura o un permiso?**
Ambos, en tablas distintas: `modulos` son asignaturas y `modulos_sistema` son
los módulos funcionales/permisos. `modulos_x_rol.modulo_id` apunta a
`modulos_sistema`; `docentes_modulos.modulo_id` apunta a `modulos`.
(Fuente: `02-roles-y-modulos.md`)

**¿Dónde está la referencia de la API?**
FastAPI genera `/docs` y `/openapi.json` al ejecutar el servicio.
(Fuente: `01-que-es-el-sistema.md`)
