from app.mappers.usuario import nombre_completo
from app.models.notificacion import Notificacion
from app.schemas.notificacion import NotificacionResponse


def notificacion_response(n: Notificacion) -> NotificacionResponse:
    return NotificacionResponse(
        id=n.id,
        remitenteId=n.remitente_id,
        nombreRemitente=nombre_completo(n.remitente),
        destinatarioId=n.destinatario_id,
        nombreDestinatario=nombre_completo(n.destinatario),
        solicitudConsultaId=n.solicitud_consulta_id,
        numeroConsulta=n.solicitudConsulta.numero_consulta,
        tipo=n.tipo,
        titulo=n.titulo,
        mensaje=n.mensaje,
        leida=n.leida,
        fechaCreacion=n.fecha_creacion,
    )