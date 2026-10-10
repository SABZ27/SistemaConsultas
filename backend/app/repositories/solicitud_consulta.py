from sqlalchemy.orm import Session

from app.models.solicitud_consulta import SolicitudConsulta
from app.models.enums import EstadoSolicitud
from app.repositories.base import RepoBase


class SolicitudConsultaRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = SolicitudConsulta

    def find_by_id(self, id_: int) -> SolicitudConsulta | None:
        return self.db.get(SolicitudConsulta, id_)

    def find_all(self) -> list[SolicitudConsulta]:
        return self.db.query(SolicitudConsulta).order_by(SolicitudConsulta.id).all()

    def find_all_by_estado(self, estado: EstadoSolicitud) -> list[SolicitudConsulta]:
        return self.db.query(SolicitudConsulta).filter(
            SolicitudConsulta.estado == estado
        ).order_by(SolicitudConsulta.id).all()

    def find_all_by_estudiante_id(self, estudiante_id: int) -> list[SolicitudConsulta]:
        return self.db.query(SolicitudConsulta).filter(
            SolicitudConsulta.estudiante_id == estudiante_id
        ).order_by(SolicitudConsulta.id).all()

    def find_all_by_docente_id(self, docente_id: int) -> list[SolicitudConsulta]:
        return self.db.query(SolicitudConsulta).filter(
            SolicitudConsulta.docente_id == docente_id
        ).order_by(SolicitudConsulta.id).all()

    def find_by_numero_consulta(self, numero: str) -> SolicitudConsulta | None:
        return self.db.query(SolicitudConsulta).filter(
            SolicitudConsulta.numero_consulta == numero
        ).first()

    def exists_by_numero_consulta(self, numero: str) -> bool:
        return self.db.query(SolicitudConsulta.id).filter(
            SolicitudConsulta.numero_consulta == numero
        ).first() is not None

    def max_id(self) -> int:
        from sqlalchemy import func
        return self.db.query(func.max(SolicitudConsulta.id)).scalar() or 0