from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.base import RepoBase


class UsuarioRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Usuario

    def find_by_id(self, id_: int) -> Usuario | None:
        return self.db.get(Usuario, id_)

    def find_by_id_and_activo_true(self, id_: int) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.id == id_, Usuario.activo.is_(True)
        ).first()

    def find_by_correo(self, correo: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.correo == correo).first()

    def find_by_identificacion_and_activo_true(self, identificacion: str) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.identificacion == identificacion, Usuario.activo.is_(True)
        ).first()

    def find_by_correo_and_activo_true(self, correo: str) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.correo == correo, Usuario.activo.is_(True)
        ).first()

    def find_by_identificacion(self, identificacion: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.identificacion == identificacion).first()

    def find_all_by_activo_true(self) -> list[Usuario]:
        return self.db.query(Usuario).filter(
            Usuario.activo.is_(True)
        ).order_by(Usuario.id).all()

    def exists_by_identificacion_and_activo_true(self, identificacion: str) -> bool:
        return self.db.query(Usuario.id).filter(
            Usuario.identificacion == identificacion, Usuario.activo.is_(True)
        ).first() is not None

    def exists_by_correo_and_activo_true(self, correo: str) -> bool:
        return self.db.query(Usuario.id).filter(
            Usuario.correo == correo, Usuario.activo.is_(True)
        ).first() is not None