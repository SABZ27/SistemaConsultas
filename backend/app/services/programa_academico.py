from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.programa_academico import programa_academico_response
from app.models.programa_academico import ProgramaAcademico
from app.repositories.programa_academico import ProgramaAcademicoRepository
from app.schemas.programa import (
    RegistroProgAcademicoRequest,
    UpdateProgAcademicoRequest,
)


class ProgramaAcademicoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProgramaAcademicoRepository(db)

    def registrar_programa(self, req: RegistroProgAcademicoRequest):
        programa_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
        if programa_existente is not None:
            raise BadRequestException("Ya existe un programa académico con ese nombre.")

        programa = ProgramaAcademico(nombre=req.nombre)
        self.repo.save(programa)
        return programa_academico_response(programa)

    def listar_programas(self):
        return [
            programa_academico_response(p)
            for p in self.repo.find_all_by_estado_true()
        ]

    def obtener_programa_por_id(self, id_programa: int):
        programa = self.repo.find_by_id_and_estado_true(id_programa)
        if programa is None:
            raise ResourceNotFoundException("Programa académico no encontrado.")
        return programa_academico_response(programa)

    def actualizar_programa(self, id_programa: int, req: UpdateProgAcademicoRequest):
        programa = self.repo.find_by_id_and_estado_true(id_programa)
        if programa is None:
            raise ResourceNotFoundException("Programa académico no encontrado.")

        if programa.nombre != req.nombre:
            programa_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if programa_existente is not None and programa_existente.id != programa.id:
                raise BadRequestException("Ya existe un programa académico con ese nombre.")
            programa.nombre = req.nombre

        return programa_academico_response(programa)

    def eliminar_programa(self, id_programa: int) -> None:
        programa = self.repo.find_by_id_and_estado_true(id_programa)
        if programa is None:
            raise ResourceNotFoundException("Programa académico no encontrado.")
        programa.estado = False