from sqlalchemy.orm import Session

from app.models.bloque import Bloque
from app.models.sede import Sede
from app.repositories.base import RepoBase


class BloqueRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Bloque

    def find_by_id(self, id_: int) -> Bloque | None:
        return self.db.get(Bloque, id_)

    def find_by_id_and_estado_true(self, id_: int) -> Bloque | None:
        return self.db.query(Bloque).filter(
            Bloque.id == id_, Bloque.estado.is_(True)
        ).first()

    def find_by_nombre_and_sede_and_estado_true(self, nombre: str, sede_id: int) -> Bloque | None:
        return self.db.query(Bloque).filter(
            Bloque.nombre == nombre,
            Bloque.sede_id == sede_id,
            Bloque.estado.is_(True),
        ).first()

    def find_all_by_estado_true(self) -> list[Bloque]:
        return self.db.query(Bloque).filter(
            Bloque.estado.is_(True)
        ).order_by(Bloque.id).all()