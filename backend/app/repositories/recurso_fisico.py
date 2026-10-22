from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.recurso_fisico import RecursoFisico
from app.repositories.base import RepoBase


class RecursoFisicoRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = RecursoFisico

    def find_by_id(self, id_: int) -> RecursoFisico | None:
        return self.db.get(RecursoFisico, id_)

    def find_by_id_and_estado_true(self, id_: int) -> RecursoFisico | None:
        return self.db.query(RecursoFisico).filter(
            RecursoFisico.id == id_, RecursoFisico.estado.is_(True)
        ).first()

    def find_by_sede_zona_nombre_and_estado_true(
        self, sede_id: int, zona_id: int | None, nombre: str
    ) -> RecursoFisico | None:
        zona_ref = zona_id if zona_id is not None else 0
        return (
            self.db.query(RecursoFisico)
            .filter(
                RecursoFisico.sede_id == sede_id,
                func.coalesce(RecursoFisico.zona_id, 0) == zona_ref,
                RecursoFisico.nombre == nombre,
                RecursoFisico.estado.is_(True),
            )
            .first()
        )

    def find_all(self, incluir_inactivos: bool = False) -> list[RecursoFisico]:
        consulta = self.db.query(RecursoFisico).order_by(RecursoFisico.nombre)
        if not incluir_inactivos:
            consulta = consulta.filter(RecursoFisico.estado.is_(True))
        return consulta.all()

    def find_all_by_sede(
        self, sede_id: int, incluir_inactivos: bool = False
    ) -> list[RecursoFisico]:
        consulta = self.db.query(RecursoFisico).filter(
            RecursoFisico.sede_id == sede_id
        ).order_by(RecursoFisico.nombre)
        if not incluir_inactivos:
            consulta = consulta.filter(RecursoFisico.estado.is_(True))
        return consulta.all()

    def find_all_by_zona(
        self, zona_id: int, incluir_inactivos: bool = False
    ) -> list[RecursoFisico]:
        consulta = self.db.query(RecursoFisico).filter(
            RecursoFisico.zona_id == zona_id
        ).order_by(RecursoFisico.nombre)
        if not incluir_inactivos:
            consulta = consulta.filter(RecursoFisico.estado.is_(True))
        return consulta.all()

    def count_by_sede_and_estado_true(self, sede_id: int) -> int:
        return (
            self.db.query(RecursoFisico)
            .filter(RecursoFisico.sede_id == sede_id, RecursoFisico.estado.is_(True))
            .count()
        )

    def count_by_zona_and_estado_true(self, zona_id: int) -> int:
        return (
            self.db.query(RecursoFisico)
            .filter(RecursoFisico.zona_id == zona_id, RecursoFisico.estado.is_(True))
            .count()
        )
