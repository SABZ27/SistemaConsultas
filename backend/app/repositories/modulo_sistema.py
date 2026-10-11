from sqlalchemy.orm import Session

from app.models.modulo_sistema import ModuloSistema
from app.repositories.base import RepoBase


class ModuloSistemaRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = ModuloSistema

    def find_by_id(self, id_: int) -> ModuloSistema | None:
        return self.db.get(ModuloSistema, id_)

    def find_by_id_and_estado_true(self, id_: int) -> ModuloSistema | None:
        return self.db.query(ModuloSistema).filter(
            ModuloSistema.id == id_, ModuloSistema.estado.is_(True)
        ).first()

    def find_by_nombre(self, nombre: str) -> ModuloSistema | None:
        return self.db.query(ModuloSistema).filter(ModuloSistema.nombre == nombre).first()

    def find_by_nombre_and_estado_true(self, nombre: str) -> ModuloSistema | None:
        return self.db.query(ModuloSistema).filter(
            ModuloSistema.nombre == nombre, ModuloSistema.estado.is_(True)
        ).first()

    def find_all_by_estado_true(self) -> list[ModuloSistema]:
        return self.db.query(ModuloSistema).filter(
            ModuloSistema.estado.is_(True)
        ).order_by(ModuloSistema.id).all()

    def find_all(self) -> list[ModuloSistema]:
        return self.db.query(ModuloSistema).order_by(ModuloSistema.id).all()

    def count_asignaciones_activas(self, modulo_id: int) -> int:
        from app.models.modulo_x_rol import ModuloXRol

        return self.db.query(ModuloXRol.id).filter(
            ModuloXRol.modulo_id == modulo_id, ModuloXRol.estado.is_(True)
        ).count()