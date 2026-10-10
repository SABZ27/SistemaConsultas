from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.models.modulo import Modulo
from app.repositories.modulo import ModuloRepository
from app.schemas.modulo import ModuloResponse, RegistroModuloRequest, UpdateModuloRequest


def _response(m: Modulo) -> ModuloResponse:
    return ModuloResponse(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        activo=m.activo,
    )


class ModuloService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ModuloRepository(db)

    def registrar(self, req: RegistroModuloRequest):
        modulo_existente = self.repo.find_by_nombre_and_activo_true(req.nombre)
        if modulo_existente is not None:
            raise BadRequestException("Ya existe un módulo con ese nombre")

        modulo = Modulo(
            nombre=req.nombre,
            descripcion=req.descripcion,
            activo=True,
        )
        self.repo.save(modulo)
        return _response(modulo)

    def listar_modulos(self):
        return [_response(m) for m in self.repo.find_all_by_activo_true()]

    def obtener_modulo_por_id(self, id_modulo: int):
        modulo = self.repo.find_by_id_and_activo_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        return _response(modulo)

    def actualizar_modulo(self, id_modulo: int, req: UpdateModuloRequest):
        modulo = self.repo.find_by_id_and_activo_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")

        if modulo.nombre != req.nombre:
            modulo_existente = self.repo.find_by_nombre_and_activo_true(req.nombre)
            if modulo_existente is not None and modulo_existente.id != modulo.id:
                raise BadRequestException("Ya existe un módulo con ese nombre.")

        modulo.nombre = req.nombre
        modulo.descripcion = req.descripcion
        return _response(modulo)

    def eliminar_modulo(self, id_modulo: int) -> None:
        modulo = self.repo.find_by_id_and_activo_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        modulo.activo = False