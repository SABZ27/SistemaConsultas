from sqlalchemy.orm import Session

from app.models.docente_modulo import DocenteModulo
from app.repositories.base import RepoBase


class DocenteModuloRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = DocenteModulo

    def find_by_id(self, id_: int) -> DocenteModulo | None:
        return self.db.get(DocenteModulo, id_)

    def find_by_id_and_estado_true(self, id_: int) -> DocenteModulo | None:
        return self.db.query(DocenteModulo).filter(
            DocenteModulo.id == id_, DocenteModulo.estado.is_(True)
        ).first()

    def find_by_docente_and_modulo(
        self, docente_id: int, modulo_id: int
    ) -> DocenteModulo | None:
        return self.db.query(DocenteModulo).filter(
            DocenteModulo.docente_id == docente_id,
            DocenteModulo.modulo_id == modulo_id,
        ).first()

    def find_all_by_estado_true(self) -> list[DocenteModulo]:
        return self.db.query(DocenteModulo).filter(
            DocenteModulo.estado.is_(True)
        ).order_by(DocenteModulo.id).all()

    def find_all(self) -> list[DocenteModulo]:
        return self.db.query(DocenteModulo).order_by(DocenteModulo.id).all()

    def find_all_by_modulo_id_and_estado_true(
        self, modulo_id: int
    ) -> list[DocenteModulo]:
        return self.db.query(DocenteModulo).filter(
            DocenteModulo.modulo_id == modulo_id,
            DocenteModulo.estado.is_(True),
        ).order_by(DocenteModulo.id).all()

    def existe_asignacion(self, docente_id: int, modulo_id: int) -> bool:
        return self.db.query(DocenteModulo.id).filter(
            DocenteModulo.docente_id == docente_id,
            DocenteModulo.modulo_id == modulo_id,
            DocenteModulo.estado.is_(True),
        ).first() is not None
