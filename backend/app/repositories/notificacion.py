from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.models.enums import TipoNotificacion
from app.repositories.base import RepoBase


class NotificacionRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Notificacion

    def find_by_id(self, id_: int) -> Notificacion | None:
        return self.db.get(Notificacion, id_)

    def find_by_destinatario_and_tipo(self, destinatario_id: int, tipo: TipoNotificacion) -> list[Notificacion]:
        return self.db.query(Notificacion).filter(
            Notificacion.destinatario_id == destinatario_id,
            Notificacion.tipo == tipo,
        ).order_by(Notificacion.fecha_creacion.desc()).all()

    def find_all_by_destinatario_id(self, destinatario_id: int) -> list[Notificacion]:
        return self.db.query(Notificacion).filter(
            Notificacion.destinatario_id == destinatario_id
        ).order_by(Notificacion.fecha_creacion.desc()).all()

    def count_by_destinatario_and_tipo_and_leida_false(self, destinatario_id: int, tipo: TipoNotificacion) -> int:
        return self.db.query(Notificacion.id).filter(
            Notificacion.destinatario_id == destinatario_id,
            Notificacion.tipo == tipo,
            Notificacion.leida.is_(False),
        ).count()

    def marcar_comentarios_leidos(self, destinatario_id: int, solicitud_consulta_id: int) -> None:
        self.db.query(Notificacion).filter(
            Notificacion.destinatario_id == destinatario_id,
            Notificacion.solicitud_consulta_id == solicitud_consulta_id,
            Notificacion.tipo == TipoNotificacion.COMENTARIO,
            Notificacion.leida.is_(False),
        ).update({"leida": True})