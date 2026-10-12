from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.periodo import periodo_response
from app.models.periodo_academico import PeriodoAcademico
from app.repositories.periodo_academico import PeriodoAcademicoRepository
from app.schemas.periodo import RegistroPeriodoRequest, UpdatePeriodoRequest


class PeriodoAcademicoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PeriodoAcademicoRepository(db)

    def listar(self, incluir_inactivos: bool = False):
        filas = (
            self.repo.find_all()
            if incluir_inactivos
            else self.repo.find_all_by_estado_true()
        )
        return [periodo_response(p) for p in filas]

    def crear(self, req: RegistroPeriodoRequest):
        if req.fechaFin <= req.fechaInicio:
            raise BadRequestException(
                "La fecha de fin debe ser posterior a la fecha de inicio."
            )
        if self.repo.find_by_nombre_and_estado_true(req.nombre) is not None:
            raise BadRequestException("Ya existe un periodo académico con ese nombre.")
        if self.repo.existe_solape(req.fechaInicio, req.fechaFin):
            raise BadRequestException(
                "Las fechas se cruzan con otro periodo académico activo."
            )

        periodo = PeriodoAcademico(
            nombre=req.nombre,
            fecha_inicio=req.fechaInicio,
            fecha_fin=req.fechaFin,
        )
        self.repo.save(periodo)
        return periodo_response(periodo)

    def obtener_por_id(self, id_: int):
        periodo = self.repo.find_by_id_and_estado_true(id_)
        if periodo is None:
            raise ResourceNotFoundException("Periodo académico no encontrado.")
        return periodo_response(periodo)

    def actualizar(self, id_: int, req: UpdatePeriodoRequest):
        periodo = self.repo.find_by_id_and_estado_true(id_)
        if periodo is None:
            raise ResourceNotFoundException("Periodo académico no encontrado.")

        if req.fechaFin <= req.fechaInicio:
            raise BadRequestException(
                "La fecha de fin debe ser posterior a la fecha de inicio."
            )
        if periodo.nombre != req.nombre:
            existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if existente is not None and existente.id != periodo.id:
                raise BadRequestException("Ya existe un periodo académico con ese nombre.")
        if self.repo.existe_solape(req.fechaInicio, req.fechaFin, excluir_id=periodo.id):
            raise BadRequestException(
                "Las fechas se cruzan con otro periodo académico activo."
            )

        periodo.nombre = req.nombre
        periodo.fecha_inicio = req.fechaInicio
        periodo.fecha_fin = req.fechaFin
        return periodo_response(periodo)

    def eliminar(self, id_: int) -> None:
        periodo = self.repo.find_by_id_and_estado_true(id_)
        if periodo is None:
            raise ResourceNotFoundException("Periodo académico no encontrado.")
        periodo.estado = False

    def activar(self, id_: int):
        periodo = self.repo.find_by_id(id_)
        if periodo is None:
            raise ResourceNotFoundException("Periodo académico no encontrado.")
        if self.repo.existe_solape(
            periodo.fecha_inicio, periodo.fecha_fin, excluir_id=periodo.id
        ):
            raise BadRequestException(
                "Las fechas se cruzan con otro periodo académico activo."
            )
        periodo.estado = True
        return periodo_response(periodo)
