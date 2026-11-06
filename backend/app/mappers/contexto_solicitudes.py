"""Contexto de respuesta de solicitudes (Bloque C · C3).

Resuelve en **dos consultas con IN**, para todas las solicitudes devueltas, los
datos que antes se cargaban fila por fila:

* la calificación activa de cada solicitud (tabla ``calificaciones_consulta``);
* la retroalimentación del docente: el comentario **activo más reciente**
  escrito por el docente asignado a esa solicitud (tabla ``comentarios``).

El modelo ``Comentario`` no tiene indicador de interno/privado; si en el futuro
se añade uno, el filtro debe aplicarse en ``construir_contexto`` para excluir
esos comentarios de ``retroalimentaciones``.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.calificacion_consulta import CalificacionConsulta
from app.models.comentario import Comentario
from app.models.solicitud_consulta import SolicitudConsulta


@dataclass
class ContextoSolicitudes:
    calificaciones: dict[int, CalificacionConsulta] = field(default_factory=dict)
    retroalimentaciones: dict[int, str] = field(default_factory=dict)


def construir_contexto(
    db: Session, solicitudes: list[SolicitudConsulta]
) -> ContextoSolicitudes:
    contexto = ContextoSolicitudes()
    ids = [s.id for s in solicitudes]
    if not ids:
        return contexto

    # Una sola consulta para todas las calificaciones activas.
    for calificacion in (
        db.query(CalificacionConsulta)
        .filter(
            CalificacionConsulta.solicitud_id.in_(ids),
            CalificacionConsulta.estado.is_(True),
        )
        .all()
    ):
        contexto.calificaciones[calificacion.solicitud_id] = calificacion

    # Una sola consulta para todos los comentarios activos; se conserva el
    # más reciente por solicitud solo si su autor es el docente asignado.
    docente_por_solicitud = {s.id: s.docente_id for s in solicitudes}
    comentarios = (
        db.query(Comentario)
        .filter(
            Comentario.solicitud_id.in_(ids),
            Comentario.estado.is_(True),
        )
        .order_by(Comentario.creado.desc(), Comentario.id.desc())
        .all()
    )
    for comentario in comentarios:
        if (
            comentario.solicitud_id not in contexto.retroalimentaciones
            and docente_por_solicitud.get(comentario.solicitud_id)
            == comentario.autor_id
        ):
            contexto.retroalimentaciones[comentario.solicitud_id] = (
                comentario.contenido
            )

    return contexto
