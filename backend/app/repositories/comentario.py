from sqlalchemy.orm import Session

from app.models.comentario import Comentario
from app.repositories.base import RepoBase


class ComentarioRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Comentario

    def find_by_id(self, id_: int) -> Comentario | None:
        return self.db.query(Comentario).filter(
            Comentario.id == id_, Comentario.estado.is_(True)
        ).first()

    def find_all_by_solicitud_id_order_fecha(self, solicitud_id: int) -> list[Comentario]:
        return self.db.query(Comentario).filter(
            Comentario.solicitud_id == solicitud_id,
            Comentario.estado.is_(True),
        ).order_by(Comentario.creado.asc()).all()

    def find_all_by_autor_id_order_fecha(self, autor_id: int) -> list[Comentario]:
        return self.db.query(Comentario).filter(
            Comentario.autor_id == autor_id,
            Comentario.estado.is_(True),
        ).order_by(Comentario.creado.desc()).all()