from sqlalchemy.orm import Session

from app.models.tipo_documento import TipoDocumento
from app.repositories.base import RepoBase


class TipoDocumentoRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = TipoDocumento

    def find_by_id(self, id_: int) -> TipoDocumento | None:
        return self.db.get(TipoDocumento, id_)

    def find_by_id_and_estado_true(self, id_: int) -> TipoDocumento | None:
        return self.db.query(TipoDocumento).filter(
            TipoDocumento.id == id_, TipoDocumento.estado.is_(True)
        ).first()

    def find_by_nombre_and_estado_true(self, nombre: str) -> TipoDocumento | None:
        return self.db.query(TipoDocumento).filter(
            TipoDocumento.nombre == nombre, TipoDocumento.estado.is_(True)
        ).first()

    def find_by_sigla_and_estado_true(self, sigla: str) -> TipoDocumento | None:
        return self.db.query(TipoDocumento).filter(
            TipoDocumento.sigla == sigla, TipoDocumento.estado.is_(True)
        ).first()

    def find_all_by_estado_true(self) -> list[TipoDocumento]:
        return self.db.query(TipoDocumento).filter(
            TipoDocumento.estado.is_(True)
        ).order_by(TipoDocumento.id).all()

    def find_all(self) -> list[TipoDocumento]:
        return self.db.query(TipoDocumento).order_by(TipoDocumento.id).all()
