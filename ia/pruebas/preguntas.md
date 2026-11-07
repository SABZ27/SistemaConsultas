# Preguntas de evaluación (Fase 1)

Este archivo es la fuente de datos de `ia/scripts/evaluar.py`. Cada caso es un
bloque que empieza con `## ID` y usa líneas `CAMPO: valor`. Los campos son:

- `TIPO`: `DOCUMENTACION`, `FUERA` o `DATOS` (los casos `DATOS` llegan en la Fase 2).
- `PREGUNTA`: texto que se envía a la API.
- `CLAVES`: palabras clave separadas por `|`. Para `FUERA`, la frase exacta
  `No encuentro esa información en la documentación disponible.`
- `FUENTE`: documento de `ia/conocimiento/` del que sale la respuesta esperada.
- `ESPERADO`: resumen de la respuesta esperada (solo para el lector humano).
- `HERRAMIENTA` y `ARGS`: solo en los casos `DATOS` (Fase 2).

La comprobación es estricta: **todas** las palabras clave deben aparecer en la
respuesta (comparación sin mayúsculas y sin tildes). No se registran preguntas
con datos personales ni secretos.

---

## DOC-01
TIPO: DOCUMENTACION
PREGUNTA: ¿Cuáles son los estados posibles de una consulta y cuál es el estado inicial?
CLAVES: PENDIENTE | EN_PROCESO | RESUELTA | RECHAZADA | CANCELADA
FUENTE: 03-flujo-y-estados.md
ESPERADO: Los cinco estados del enum EstadoSolicitud; el inicial es PENDIENTE.

## DOC-02
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué transiciones de estado están permitidas desde PENDIENTE?
CLAVES: EN_PROCESO | RECHAZADA | CANCELADA
FUENTE: 03-flujo-y-estados.md
ESPERADO: Desde PENDIENTE solo se puede pasar a EN_PROCESO, RECHAZADA o CANCELADA.

## DOC-03
TIPO: DOCUMENTACION
PREGUNTA: ¿Quién puede calificar una consulta y en qué estado debe estar?
CLAVES: estudiante | RESUELTA | 403
FUENTE: 05-calificacion.md
ESPERADO: Solo el estudiante dueño; la consulta debe estar RESUELTA; un docente recibe 403.

## DOC-04
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué campos tiene una calificación y qué límites tienen?
CLAVES: puntaje | 500
FUENTE: 05-calificacion.md
ESPERADO: puntaje entero de 1 a 5 y comentario opcional de hasta 500 caracteres.

## DOC-05
TIPO: DOCUMENTACION
PREGUNTA: ¿Puede un docente calificar una consulta que atendió?
CLAVES: 403 | estudiante
FUENTE: 05-calificacion.md
ESPERADO: No; recibe 403 porque la calificación es exclusiva del estudiante dueño.

## DOC-06
TIPO: DOCUMENTACION
PREGUNTA: ¿En qué estado se pueden crear comentarios?
CLAVES: EN_PROCESO | comentarios
FUENTE: 03-flujo-y-estados.md
ESPERADO: Solo en EN_PROCESO; pueden comentar los participantes.

## DOC-07
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué campos son obligatorios al crear una consulta?
CLAVES: prioridad | asunto | docenteId | moduloId
FUENTE: 04-crear-una-consulta.md
ESPERADO: prioridad, asunto, descripcion, fechaConsulta, horaConsulta, docenteId y moduloId.

## DOC-08
TIPO: DOCUMENTACION
PREGUNTA: ¿Cómo se genera el número de consulta?
CLAVES: SC- | unico
FUENTE: 04-crear-una-consulta.md
ESPERADO: Formato SC-<año>-<6 dígitos>, único, con hasta 5 reintentos.

## DOC-09
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué ocurre si el servicio de festivos no responde al crear una consulta?
CLAVES: 503 | fail-closed
FUENTE: 07-festivos-y-fechas.md
ESPERADO: Se rechaza con 503 (fail-closed); no se crea sin validar la fecha.

## DOC-10
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué festivos se trasladan al lunes siguiente por la Ley Emiliani?
CLAVES: Ascension | Corpus Christi | lunes
FUENTE: 07-festivos-y-fechas.md
ESPERADO: Solo Ascension Day y Corpus Christi; ningún otro festivo se mueve.

## DOC-11
TIPO: DOCUMENTACION
PREGUNTA: ¿Cuál es la longitud mínima y máxima de una contraseña?
CLAVES: 10 | 72 | bytes
FUENTE: 08-politica-de-contrasenas.md
ESPERADO: Mínimo 10 caracteres y máximo 72 bytes en UTF-8.

## DOC-12
TIPO: DOCUMENTACION
PREGUNTA: ¿Cuántos intentos fallidos de login bloquean la pareja correo+IP y cuánto dura el bloqueo?
CLAVES: 5 | 15 min | Retry-After
FUENTE: 08-politica-de-contrasenas.md
ESPERADO: 5 fallos en 15 min; bloqueo de 15 min; la respuesta 429 incluye Retry-After.

## DOC-13
TIPO: DOCUMENTACION
PREGUNTA: ¿Cuánto dura el token JWT de usuario y con qué algoritmo se firma?
CLAVES: 30 minutos | HS256
FUENTE: 08-politica-de-contrasenas.md
ESPERADO: 30 minutos (JWT_EXPIRATION_MINUTES), firmado con HS256.

## DOC-14
TIPO: DOCUMENTACION
PREGUNTA: ¿Qué token acepta POST /correos y qué recibe un token de usuario?
CLAVES: SERVICIO | 5 minutos | 403
FUENTE: 06-notificaciones-y-correos.md
ESPERADO: Token interno rol SERVICIO de 5 minutos; un token de usuario recibe 403.

## DOC-15
TIPO: DOCUMENTACION
PREGUNTA: ¿Cuáles son los tres roles del sistema?
CLAVES: ESTUDIANTE | DOCENTE | ADMINISTRADOR
FUENTE: 02-roles-y-modulos.md
ESPERADO: ESTUDIANTE, DOCENTE y ADMINISTRADOR.

---

## FUERA-01
TIPO: FUERA
PREGUNTA: ¿Cuál es la capital de Francia?
CLAVES: No encuentro esa información en la documentación disponible.
FUENTE: (ninguno)
ESPERADO: Debe responder exactamente la frase de "no encuentro".

## FUERA-02
TIPO: FUERA
PREGUNTA: ¿Quién ganó la última Copa Mundial de Fútbol?
CLAVES: No encuentro esa información en la documentación disponible.
FUENTE: (ninguno)
ESPERADO: Debe responder exactamente la frase de "no encuentro".

## FUERA-03
TIPO: FUERA
PREGUNTA: Escribe un chiste sobre programadores y explica cómo funciona un motor de combustión.
CLAVES: No encuentro esa información en la documentación disponible.
FUENTE: (ninguno)
ESPERADO: Tema ajeno al sistema: debe responder exactamente la frase de "no encuentro".
