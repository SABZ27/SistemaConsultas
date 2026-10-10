from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.models.sede import Sede
from app.repositories.sede import SedeRepository
from app.schemas.sede import RegistroSedeRequest, SedeResponse, UpdateSedeRequest


def _response(s: Sede) -> SedeResponse:
    return SedeResponse(id=s.id, nombre=s.nombre, estado=s.estado)


class SedeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SedeRepository(db)

    def registrar_sede(self, req: RegistroSedeRequest):
        if self.repo.exists_by_nombre_and_estado_true(req.nombre):
            raise BadRequestException("Ya existe una sede con ese nombre.")

        sede = Sede(nombre=req.nombre)
        self.repo.save(sede)
        return _response(sede)

    def listar_sedes(self):
        return [_response(s) for s in self.repo.find_all_by_estado_true()]

    def obtener_sede_por_id(self, id_sede: int):
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")
        return _response(sede)

    def actualizar_sede(self, id_sede: int, req: UpdateSedeRequest):
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")

        if sede.nombre != req.nombre:
            sede_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if sede_existente is not None and sede_existente.id != sede.id:
                raise BadRequestException("Ya existe una sede con ese nombre.")
            sede.nombre = req.nombre

        return _response(sede)

    def eliminar_sede(self, id_sede: int) -> None:
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")
        sede.estado = False