from app.mappers.usuario import nombre_completo
from app.models.comentario import Comentario
from app.schemas.comentario import ComentarioResponse


def comentario_response(c: Comentario) -> ComentarioResponse:
    return ComentarioResponse(
        id=c.id,
        autorId=c.autor_id,
        nombreAutor=nombre_completo(c.autor),
        consultaId=c.solicitud_id,
        numeroConsulta=c.solicitudConsulta.numero_consulta,
        contenido=c.contenido,
        fechaCreacion=c.fecha_creacion,
        editado=c.editado,
    )