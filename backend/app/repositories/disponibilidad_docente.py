from datetime import time

from sqlalchemy.orm import Session

from app.models.disponibilidad_docente import DisponibilidadDocente
from app.repositories.base import RepoBase


class DisponibilidadDocenteRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = DisponibilidadDocente

    def find_by_id(self, id_: int) -> DisponibilidadDocente | None:
        return self.db.get(DisponibilidadDocente, id_)

    def find_by_id_and_estado_true(self, id_: int) -> DisponibilidadDocente | None:
        return self.db.query(DisponibilidadDocente).filter(
            DisponibilidadDocente.id == id_,
            DisponibilidadDocente.estado.is_(True),
        ).first()

    def find_by_docente_dia_hora(
        self, docente_id: int, dia_semana: int, hora_inicio: time
    ) -> DisponibilidadDocente | None:
        return self.db.query(DisponibilidadDocente).filter(
            DisponibilidadDocente.docente_id == docente_id,
            DisponibilidadDocente.dia_semana == dia_semana,
            DisponibilidadDocente.hora_inicio == hora_inicio,
        ).first()

    def find_all_by_estado_true(self) -> list[DisponibilidadDocente]:
        return self.db.query(DisponibilidadDocente).filter(
            DisponibilidadDocente.estado.is_(True)
        ).order_by(DisponibilidadDocente.id).all()

    def find_all(self) -> list[DisponibilidadDocente]:
        return self.db.query(DisponibilidadDocente).order_by(
            DisponibilidadDocente.id
        ).all()

    def find_all_by_docente_id_and_estado_true(
        self, docente_id: int
    ) -> list[DisponibilidadDocente]:
        return self.db.query(DisponibilidadDocente).filter(
            DisponibilidadDocente.docente_id == docente_id,
            DisponibilidadDocente.estado.is_(True),
        ).order_by(DisponibilidadDocente.dia_semana, DisponibilidadDocente.hora_inicio).all()

    def find_all_by_docente_id(self, docente_id: int) -> list[DisponibilidadDocente]:
        return self.db.query(DisponibilidadDocente).filter(
            DisponibilidadDocente.docente_id == docente_id
        ).order_by(DisponibilidadDocente.dia_semana, DisponibilidadDocente.hora_inicio).all()

    def existe_solape(
        self,
        docente_id: int,
        dia_semana: int,
        hora_inicio: time,
        hora_fin: time,
        excluir_id: int | None = None,
    ) -> bool:
        consulta = self.db.query(DisponibilidadDocente.id).filter(
            DisponibilidadDocente.docente_id == docente_id,
            DisponibilidadDocente.dia_semana == dia_semana,
            DisponibilidadDocente.estado.is_(True),
            DisponibilidadDocente.hora_inicio < hora_fin,
            DisponibilidadDocente.hora_fin > hora_inicio,
        )
        if excluir_id is not None:
            consulta = consulta.filter(DisponibilidadDocente.id != excluir_id)
        return consulta.first() is not None

    def tiene_disponibilidad(self, docente_id: int, dia_semana: int, hora: time) -> bool:
        return self.db.query(DisponibilidadDocente.id).filter(
            DisponibilidadDocente.docente_id == docente_id,
            DisponibilidadDocente.dia_semana == dia_semana,
            DisponibilidadDocente.estado.is_(True),
            DisponibilidadDocente.hora_inicio <= hora,
            DisponibilidadDocente.hora_fin >= hora,
        ).first() is not None
