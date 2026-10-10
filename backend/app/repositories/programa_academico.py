from sqlalchemy.orm import Session

from app.models.programa_academico import ProgramaAcademico
from app.repositories.base import RepoBase


class ProgramaAcademicoRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = ProgramaAcademico

    def find_by_id(self, id_: int) -> ProgramaAcademico | None:
        return self.db.get(ProgramaAcademico, id_)

    def find_by_id_and_activo_true(self, id_: int) -> ProgramaAcademico | None:
        return self.db.query(ProgramaAcademico).filter(
            ProgramaAcademico.id == id_, ProgramaAcademico.activo.is_(True)
        ).first()

    def find_by_nombre_and_activo_true(self, nombre: str) -> ProgramaAcademico | None:
        return self.db.query(ProgramaAcademico).filter(
            ProgramaAcademico.nombre == nombre, ProgramaAcademico.activo.is_(True)
        ).first()

    def find_all_by_activo_true(self) -> list[ProgramaAcademico]:
        return self.db.query(ProgramaAcademico).filter(
            ProgramaAcademico.activo.is_(True)
        ).order_by(ProgramaAcademico.id).all()