from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.calificacion_consulta import CalificacionConsulta
from app.models.solicitud_consulta import SolicitudConsulta
from app.repositories.base import RepoBase


class CalificacionConsultaRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = CalificacionConsulta

    def find_by_id(self, id_: int) -> CalificacionConsulta | None:
        return self.db.get(CalificacionConsulta, id_)

    def find_by_id_and_estado_true(self, id_: int) -> CalificacionConsulta | None:
        return self.db.query(CalificacionConsulta).filter(
            CalificacionConsulta.id == id_, CalificacionConsulta.estado.is_(True)
        ).first()

    def find_by_solicitud_id_and_estado_true(
        self, solicitud_id: int
    ) -> CalificacionConsulta | None:
        return self.db.query(CalificacionConsulta).filter(
            CalificacionConsulta.solicitud_id == solicitud_id,
            CalificacionConsulta.estado.is_(True),
        ).first()

    def promedio_by_docente_id(self, docente_id: int) -> tuple[float, int]:
        fila = (
            self.db.query(
                func.avg(CalificacionConsulta.puntaje),
                func.count(CalificacionConsulta.id),
            )
            .join(
                SolicitudConsulta,
                SolicitudConsulta.id == CalificacionConsulta.solicitud_id,
            )
            .filter(
                SolicitudConsulta.docente_id == docente_id,
                SolicitudConsulta.estado.is_(True),
                CalificacionConsulta.estado.is_(True),
            )
            .one()
        )
        promedio, total = fila
        return (float(promedio) if promedio is not None else 0.0, int(total or 0))
