from sqlalchemy.orm import Session

from app.models.evento_solicitud import EventoSolicitud
from app.repositories.base import RepoBase


class EventoSolicitudRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = EventoSolicitud

    def find_all_by_solicitud_id_order_fecha(self, solicitud_id: int) -> list[EventoSolicitud]:
        return self.db.query(EventoSolicitud).filter(
            EventoSolicitud.solicitud_id == solicitud_id,
            EventoSolicitud.estado.is_(True),
        ).order_by(EventoSolicitud.fecha_evento.desc()).all()

    def find_all_by_solicitud_id_and_usuario_id_order_fecha(
        self, solicitud_id: int, usuario_id: int
    ) -> list[EventoSolicitud]:
        return self.db.query(EventoSolicitud).filter(
            EventoSolicitud.solicitud_id == solicitud_id,
            EventoSolicitud.usuario_id == usuario_id,
            EventoSolicitud.estado.is_(True),
        ).order_by(EventoSolicitud.fecha_evento.desc()).all()

    def has_evento(self, solicitud_id: int, tipo_evento) -> bool:
        return self.db.query(EventoSolicitud.id).filter(
            EventoSolicitud.solicitud_id == solicitud_id,
            EventoSolicitud.tipo_evento == tipo_evento,
            EventoSolicitud.estado.is_(True),
        ).first() is not None