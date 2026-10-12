from app.models.calificacion_consulta import CalificacionConsulta
from app.schemas.calificacion import CalificacionResponse


def calificacion_response(c: CalificacionConsulta) -> CalificacionResponse:
    solicitud = c.solicitud
    return CalificacionResponse(
        id=c.id,
        solicitudId=c.solicitud_id,
        puntaje=c.puntaje,
        comentario=c.comentario,
        docenteId=solicitud.docente_id,
        estudianteId=solicitud.estudiante_id,
        fechaCreacion=c.creado,
    )
