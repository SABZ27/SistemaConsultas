from sqlalchemy.orm import Session

from app.models.recurso_fisico import RecursoFisico
from app.repositories.base import RepoBase


class RecursoFisicoRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = RecursoFisico

    def find_by_id(self, id_: int) -> RecursoFisico | None:
        return self.db.get(RecursoFisico, id_)

    def find_by_id_and_activo_true(self, id_: int) -> RecursoFisico | None:
        return self.db.query(RecursoFisico).filter(
            RecursoFisico.id == id_, RecursoFisico.activo.is_(True)
        ).first()

    def find_by_nombre_and_bloque_and_activo_true(
        self, nombre: str, bloque_id: int
    ) -> RecursoFisico | None:
        return self.db.query(RecursoFisico).filter(
            RecursoFisico.nombre == nombre,
            RecursoFisico.bloque_id == bloque_id,
            RecursoFisico.activo.is_(True),
        ).first()

    def find_all_by_activo_true(self) -> list[RecursoFisico]:
        return self.db.query(RecursoFisico).filter(
            RecursoFisico.activo.is_(True)
        ).order_by(RecursoFisico.id).all()