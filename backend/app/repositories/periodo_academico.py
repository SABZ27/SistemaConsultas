from datetime import date

from sqlalchemy.orm import Session

from app.models.periodo_academico import PeriodoAcademico
from app.repositories.base import RepoBase


class PeriodoAcademicoRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = PeriodoAcademico

    def find_by_id(self, id_: int) -> PeriodoAcademico | None:
        return self.db.get(PeriodoAcademico, id_)

    def find_by_id_and_estado_true(self, id_: int) -> PeriodoAcademico | None:
        return self.db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == id_, PeriodoAcademico.estado.is_(True)
        ).first()

    def find_by_nombre_and_estado_true(self, nombre: str) -> PeriodoAcademico | None:
        return self.db.query(PeriodoAcademico).filter(
            PeriodoAcademico.nombre == nombre, PeriodoAcademico.estado.is_(True)
        ).first()

    def find_all_by_estado_true(self) -> list[PeriodoAcademico]:
        return self.db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado.is_(True)
        ).order_by(PeriodoAcademico.id).all()

    def find_all(self) -> list[PeriodoAcademico]:
        return self.db.query(PeriodoAcademico).order_by(PeriodoAcademico.id).all()

    def find_vigente(self, fecha: date) -> PeriodoAcademico | None:
        return self.db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado.is_(True),
            PeriodoAcademico.fecha_inicio <= fecha,
            PeriodoAcademico.fecha_fin >= fecha,
        ).first()

    def existe_solape(
        self, fecha_inicio: date, fecha_fin: date, excluir_id: int | None = None
    ) -> bool:
        consulta = self.db.query(PeriodoAcademico.id).filter(
            PeriodoAcademico.estado.is_(True),
            PeriodoAcademico.fecha_inicio <= fecha_fin,
            PeriodoAcademico.fecha_fin >= fecha_inicio,
        )
        if excluir_id is not None:
            consulta = consulta.filter(PeriodoAcademico.id != excluir_id)
        return consulta.first() is not None
