from sqlalchemy.orm import Session

from app.models.modulo import Modulo
from app.repositories.base import RepoBase


class ModuloRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Modulo

    def find_by_id(self, id_: int) -> Modulo | None:
        return self.db.get(Modulo, id_)

    def find_by_id_and_activo_true(self, id_: int) -> Modulo | None:
        return self.db.query(Modulo).filter(
            Modulo.id == id_, Modulo.activo.is_(True)
        ).first()

    def find_by_nombre_and_activo_true(self, nombre: str) -> Modulo | None:
        return self.db.query(Modulo).filter(
            Modulo.nombre == nombre, Modulo.activo.is_(True)
        ).first()

    def find_all_by_activo_true(self) -> list[Modulo]:
        return self.db.query(Modulo).filter(
            Modulo.activo.is_(True)
        ).order_by(Modulo.id).all()