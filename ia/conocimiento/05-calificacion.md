# Cómo se califica una consulta

## Quién califica y cuándo

La **calificación** la crea el **estudiante dueño** de la consulta mediante
`POST /solicitudes-consultas/{id}/calificacion` (201).

Reglas reales del servicio (`CalificacionConsultaService.calificar`):

- Si el usuario no es el dueño (`usuario.id != solicitud.estudiante_id`)
  → **403** `Solo el estudiante dueño puede calificar la consulta.`. **No hay
  comprobación explícita de rol**: se verifica la pertenencia; como el creador
  siempre es `ESTUDIANTE`, un **DOCENTE** (o un administrador, u otro usuario)
  que lo intente recibe **403**.
- La consulta debe estar en estado **`RESUELTA`**; si no → **400**
  `Solo se puede calificar una consulta con estado RESUELTA.`.
- Solo puede existir **una** calificación activa por solicitud (índice único
  parcial sobre `solicitud_id` con `WHERE estado`). Si ya existe → 400
  `La consulta ya fue calificada.`.

## Campos

`CalificacionRequest`:

| Campo | Regla |
|---|---|
| `puntaje` | entero de **1 a 5** (`Field(ge=1, le=5)` y `CHECK (puntaje >= 1 AND puntaje <= 5)`) |
| `comentario` | texto opcional, máximo **500** caracteres |

Los nombres reales son **`puntaje`** y **`comentario`**. No existe un campo
`nota`, y la palabra *retroalimentación* **no pertenece a la calificación**.

## Lectura y promedio

- `GET /solicitudes-consultas/{id}/calificacion`: lo puede ver un participante
  (estudiante o docente) o un gestor con `GESTION_SOLICITUDES`; 404 si no hay.
- `GET /docentes/{id_docente}/calificaciones/promedio`: devuelve
  `round(avg(puntaje), 2)` y el `total`, filtrando solicitudes y calificaciones
  activas. Solo requiere estar autenticado.

## Inmutabilidad

**No existen** endpoints `PUT`, `PATCH` ni `DELETE` de calificaciones, ni
métodos de actualización o eliminación en su servicio/repositorio. Por API la
calificación es **inmutable e indeleble** (solo se lee).

## Calificación frente a retroalimentación (distinción clave)

Son **dos entidades distintas**:

| | Calificación | Retroalimentación / comentarios |
|---|---|---|
| Entidad | `calificaciones_consulta` | `comentarios` |
| Autor | estudiante dueño | cualquier participante (estudiante o docente) |
| Estado requerido | **`RESUELTA`** | **`EN_PROCESO`** |
| Contenido | `puntaje` 1–5 + `comentario` ≤500 | `contenido` (sin máximo) |
| Unicidad | una por solicitud | muchos por solicitud |
| Edición / borrado | no | editar solo el autor; borrar autor o gestor |

El campo `retroalimentacionDocente` que aparece en `SolicitudConsultaResponse`
**no es una entidad**: es una cadena derivada con el comentario **activo más
reciente cuyo autor es el docente asignado** de esa solicitud. La notificación
de tipo `COMENTARIO` **no genera correo**.
