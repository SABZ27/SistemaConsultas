from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.base import RepoBase


class UsuarioRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = Usuario

    def find_by_id(self, id_: int) -> Usuario | None:
        return self.db.get(Usuario, id_)

    def find_by_id_and_estado_true(self, id_: int) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.id == id_, Usuario.estado.is_(True)
        ).first()

    def find_by_correo(self, correo: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.correo == correo).first()

    def find_by_identificacion_and_estado_true(self, identificacion: str) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.identificacion == identificacion, Usuario.estado.is_(True)
        ).first()

    def find_by_correo_and_estado_true(self, correo: str) -> Usuario | None:
        return self.db.query(Usuario).filter(
            Usuario.correo == correo, Usuario.estado.is_(True)
        ).first()

    def find_by_identificacion(self, identificacion: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.identificacion == identificacion).first()

    def find_all_by_estado_true(self) -> list[Usuario]:
        return self.db.query(Usuario).filter(
            Usuario.estado.is_(True)
        ).order_by(Usuario.id).all()

    def find_all(self) -> list[Usuario]:
        return self.db.query(Usuario).order_by(Usuario.id).all()

    def find_docentes_activos(self) -> list[Usuario]:
        from app.models.enums import Rol
        from app.models.rol import Rol as RolEntidad

        return (
            self.db.query(Usuario)
            .join(RolEntidad, RolEntidad.id == Usuario.rol_id)
            .filter(
                Usuario.estado.is_(True),
                RolEntidad.nombre == Rol.DOCENTE.value,
            )
            .order_by(Usuario.id)
            .all()
        )

    def find_admin_activo(self) -> Usuario | None:
        from app.models.enums import Rol
        from app.models.rol import Rol as RolEntidad

        return (
            self.db.query(Usuario)
            .join(RolEntidad, RolEntidad.id == Usuario.rol_id)
            .filter(RolEntidad.nombre == Rol.ADMINISTRADOR.value)
            .first()
        )

    def exists_by_identificacion_and_estado_true(self, identificacion: str) -> bool:
        return self.db.query(Usuario.id).filter(
            Usuario.identificacion == identificacion, Usuario.estado.is_(True)
        ).first() is not None

    def exists_by_correo_and_estado_true(self, correo: str) -> bool:
        return self.db.query(Usuario.id).filter(
            Usuario.correo == correo, Usuario.estado.is_(True)
        ).first() is not None