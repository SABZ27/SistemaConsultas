from sqlalchemy.orm import Session

from app.models.zona import Zona
from app.repositories.base import RepoBase


class ZonaRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Zona

    def find_by_id(self, id_: int) -> Zona | None:
        return self.db.get(Zona, id_)

    def find_by_id_and_estado_true(self, id_: int) -> Zona | None:
        return self.db.query(Zona).filter(
            Zona.id == id_, Zona.estado.is_(True)
        ).first()

    def find_by_sede_and_nombre_and_estado_true(
        self, sede_id: int, nombre: str
    ) -> Zona | None:
        return self.db.query(Zona).filter(
            Zona.sede_id == sede_id, Zona.nombre == nombre, Zona.estado.is_(True)
        ).first()

    def find_all(self, incluir_inactivos: bool = False) -> list[Zona]:
        consulta = self.db.query(Zona).order_by(Zona.sede_id, Zona.nombre)
        if not incluir_inactivos:
            consulta = consulta.filter(Zona.estado.is_(True))
        return consulta.all()

    def find_all_by_sede(self, sede_id: int, incluir_inactivos: bool = False) -> list[Zona]:
        consulta = self.db.query(Zona).filter(Zona.sede_id == sede_id).order_by(Zona.nombre)
        if not incluir_inactivos:
            consulta = consulta.filter(Zona.estado.is_(True))
        return consulta.all()

    def count_by_sede_and_estado_true(self, sede_id: int) -> int:
        return (
            self.db.query(Zona)
            .filter(Zona.sede_id == sede_id, Zona.estado.is_(True))
            .count()
        )
