from sqlalchemy.orm import Session

from app.models.modulo_sistema import ModuloSistema
from app.models.modulo_x_rol import ModuloXRol
from app.repositories.base import RepoBase


class ModuloXRolRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = ModuloXRol

    def existe_permiso_activo(self, rol_id: int, nombre_modulo: str) -> bool:
        return (
            self.db.query(ModuloXRol.id)
            .join(ModuloSistema, ModuloSistema.id == ModuloXRol.modulo_id)
            .filter(
                ModuloXRol.rol_id == rol_id,
                ModuloXRol.estado.is_(True),
                ModuloSistema.nombre == nombre_modulo,
                ModuloSistema.estado.is_(True),
            )
            .first()
            is not None
        )

    def activos_por_rol(self, rol_id: int) -> list[ModuloSistema]:
        return (
            self.db.query(ModuloSistema)
            .join(ModuloXRol, ModuloXRol.modulo_id == ModuloSistema.id)
            .filter(
                ModuloXRol.rol_id == rol_id,
                ModuloXRol.estado.is_(True),
                ModuloSistema.estado.is_(True),
            )
            .order_by(ModuloSistema.id)
            .all()
        )

    def find_by_rol_id_and_estado_true(self, rol_id: int) -> list[ModuloXRol]:
        return (
            self.db.query(ModuloXRol)
            .filter(ModuloXRol.rol_id == rol_id, ModuloXRol.estado.is_(True))
            .all()
        )

    def find_by_rol_and_modulo(self, rol_id: int, modulo_id: int) -> ModuloXRol | None:
        return self.db.query(ModuloXRol).filter(
            ModuloXRol.rol_id == rol_id, ModuloXRol.modulo_id == modulo_id
        ).first()