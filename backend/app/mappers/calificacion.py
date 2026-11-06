from app.models.calificacion_consulta import CalificacionConsulta
from app.mappers.usuario import nombre_completo
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
        # Solo nombres legibles: no se exponen identificacion ni correo.
        numeroConsulta=solicitud.numero_consulta,
        nombreEstudiante=nombre_completo(solicitud.estudiante),
        nombreDocente=nombre_completo(solicitud.docente),
        fechaActualizacion=c.actualizado,
    )
