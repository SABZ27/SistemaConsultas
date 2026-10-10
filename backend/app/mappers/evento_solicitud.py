from app.mappers.usuario import nombre_completo
from app.models.evento_solicitud import EventoSolicitud
from app.schemas.evento_solicitud import EventoSolicitudResponse


def evento_solicitud_response(e: EventoSolicitud) -> EventoSolicitudResponse:
    return EventoSolicitudResponse(
        id=e.id,
        solicitudId=e.solicitud_id,
        usuarioId=e.usuario_id,
        nombreUsuario=nombre_completo(e.usuario),
        tipoEvento=e.tipo_evento,
        descripcion=e.descripcion,
        fechaEvento=e.fecha_evento,
    )