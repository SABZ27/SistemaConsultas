from sqlalchemy.orm import Session

from app.models.sede import Sede
from app.repositories.base import RepoBase


class SedeRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Sede

    def find_by_id(self, id_: int) -> Sede | None:
        return self.db.get(Sede, id_)

    def find_by_id_and_estado_true(self, id_: int) -> Sede | None:
        return self.db.query(Sede).filter(
            Sede.id == id_, Sede.estado.is_(True)
        ).first()

    def find_by_nombre_and_estado_true(self, nombre: str) -> Sede | None:
        return self.db.query(Sede).filter(
            Sede.nombre == nombre, Sede.estado.is_(True)
        ).first()

    def exists_by_nombre_and_estado_true(self, nombre: str) -> bool:
        return self.db.query(Sede.id).filter(
            Sede.nombre == nombre, Sede.estado.is_(True)
        ).first() is not None

    def find_all_by_estado_true(self) -> list[Sede]:
        return self.db.query(Sede).filter(
            Sede.estado.is_(True)
        ).order_by(Sede.id).all()