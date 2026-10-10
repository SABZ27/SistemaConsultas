from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.recurso_fisico import recurso_fisico_response
from app.models.recurso_fisico import RecursoFisico
from app.repositories.bloque import BloqueRepository
from app.repositories.recurso_fisico import RecursoFisicoRepository
from app.schemas.recurso_fisico import (
    RegistroRecursoFisicoRequest,
    UpdateRecursoFisicoRequest,
)


class RecursoFisicoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecursoFisicoRepository(db)
        self.bloque_repo = BloqueRepository(db)

    def registrar_recurso_fisico(self, req: RegistroRecursoFisicoRequest):
        bloque = self.bloque_repo.find_by_id_and_estado_true(req.bloqueId)
        if bloque is None:
            raise ResourceNotFoundException("No existe ese bloque.")

        if (
            self.repo.find_by_nombre_and_bloque_and_estado_true(req.nombre, req.bloqueId)
            is not None
        ):
            raise BadRequestException("Ya existe un RF con ese nombre en este bloque.")

        recurso = RecursoFisico(
            nombre=req.nombre,
            tipo=req.tipo,
            bloque=bloque,
        )
        self.repo.save(recurso)
        return recurso_fisico_response(recurso)

    def listar_recursos_fisicos(self):
        return [
            recurso_fisico_response(r)
            for r in self.repo.find_all_by_estado_true()
        ]

    def obtener_recurso_fisico_por_id(self, id_recurso: int):
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        return recurso_fisico_response(recurso)

    def actualizar_recurso_fisico(self, id_recurso: int, req: UpdateRecursoFisicoRequest):
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")

        if recurso.nombre != req.nombre:
            recurso_existente = self.repo.find_by_nombre_and_bloque_and_estado_true(
                req.nombre, recurso.bloque_id
            )
            if recurso_existente is not None and recurso_existente.id != recurso.id:
                raise BadRequestException(
                    "Ya existe un recurso físico con ese nombre en este bloque."
                )
            recurso.nombre = req.nombre

        return recurso_fisico_response(recurso)

    def eliminar_recurso_fisico(self, id_recurso: int) -> None:
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        recurso.estado = False