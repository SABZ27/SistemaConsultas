from sqlalchemy.orm import Session

from app.models.rol import Rol
from app.models.usuario import Usuario
from app.repositories.base import RepoBase


class RolRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Rol

    def find_by_id(self, id_: int) -> Rol | None:
        return self.db.get(Rol, id_)

    def find_by_id_and_estado_true(self, id_: int) -> Rol | None:
        return self.db.query(Rol).filter(Rol.id == id_, Rol.estado.is_(True)).first()

    def find_by_nombre(self, nombre: str) -> Rol | None:
        return self.db.query(Rol).filter(Rol.nombre == nombre).first()

    def find_by_nombre_and_estado_true(self, nombre: str) -> Rol | None:
        return self.db.query(Rol).filter(
            Rol.nombre == nombre, Rol.estado.is_(True)
        ).first()

    def find_all_by_estado_true(self) -> list[Rol]:
        return self.db.query(Rol).filter(Rol.estado.is_(True)).order_by(Rol.id).all()

    def find_all(self) -> list[Rol]:
        return self.db.query(Rol).order_by(Rol.id).all()

    def count_usuarios_activos(self, rol_id: int) -> int:
        return self.db.query(Usuario.id).filter(
            Usuario.rol_id == rol_id, Usuario.estado.is_(True)
        ).count()