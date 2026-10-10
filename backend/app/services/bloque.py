from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.bloque import bloque_response
from app.models.bloque import Bloque
from app.repositories.bloque import BloqueRepository
from app.repositories.sede import SedeRepository
from app.schemas.bloque import RegistroBloqueRequest, UpdateBloqueRequest


class BloqueService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BloqueRepository(db)
        self.sede_repo = SedeRepository(db)

    def registrar_bloque(self, req: RegistroBloqueRequest):
        sede = self.sede_repo.find_by_id_and_estado_true(req.sedeId)
        if sede is None:
            raise ResourceNotFoundException("La sede no existe.")

        if self.repo.find_by_nombre_and_sede_and_estado_true(req.nombre, req.sedeId) is not None:
            raise BadRequestException("Ya existe un bloque con ese nombre en esta sede.")

        bloque = Bloque(nombre=req.nombre, sede=sede)
        self.repo.save(bloque)
        return bloque_response(bloque)

    def listar_bloques(self):
        return [bloque_response(b) for b in self.repo.find_all_by_estado_true()]

    def obtener_bloque_por_id(self, id_bloque: int):
        bloque = self.repo.find_by_id_and_estado_true(id_bloque)
        if bloque is None:
            raise ResourceNotFoundException("Bloque no encontrado.")
        return bloque_response(bloque)

    def actualizar_bloque(self, id_bloque: int, req: UpdateBloqueRequest):
        bloque = self.repo.find_by_id_and_estado_true(id_bloque)
        if bloque is None:
            raise ResourceNotFoundException("Bloque no encontrado.")

        if bloque.nombre != req.nombre:
            bloque_existente = self.repo.find_by_nombre_and_sede_and_estado_true(
                req.nombre, bloque.sede_id
            )
            if bloque_existente is not None and bloque_existente.id != bloque.id:
                raise BadRequestException("Ya existe un bloque con ese nombre en esta sede.")
            bloque.nombre = req.nombre

        return bloque_response(bloque)

    def eliminar_bloque(self, id_bloque: int) -> None:
        bloque = self.repo.find_by_id_and_estado_true(id_bloque)
        if bloque is None:
            raise ResourceNotFoundException("Bloque no encontrado.")
        bloque.estado = False