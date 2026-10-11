from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.modulo_sistema import modulo_sistema_response
from app.models.modulo_sistema import ModuloSistema
from app.repositories.modulo_sistema import ModuloSistemaRepository
from app.schemas.modulo_sistema import (
    RegistroModuloSistemaRequest,
    UpdateModuloSistemaRequest,
)


class ModuloSistemaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ModuloSistemaRepository(db)

    def listar_modulos(self, incluir_inactivos: bool = False):
        filas = self.repo.find_all() if incluir_inactivos else self.repo.find_all_by_estado_true()
        return [modulo_sistema_response(m) for m in filas]

    def crear_modulo(self, req: RegistroModuloSistemaRequest):
        modulo_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
        if modulo_existente is not None:
            raise BadRequestException("Ya existe un módulo con ese nombre.")
        modulo = ModuloSistema(
            nombre=req.nombre,
            descripcion=req.descripcion,
            ruta=req.ruta,
            icono=req.icono,
        )
        self.repo.save(modulo)
        return modulo_sistema_response(modulo)

    def obtener_modulo_por_id(self, id_modulo: int):
        modulo = self.repo.find_by_id_and_estado_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        return modulo_sistema_response(modulo)

    def actualizar_modulo(self, id_modulo: int, req: UpdateModuloSistemaRequest):
        modulo = self.repo.find_by_id_and_estado_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")

        if modulo.nombre != req.nombre:
            modulo_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if modulo_existente is not None and modulo_existente.id != modulo.id:
                raise BadRequestException("Ya existe un módulo con ese nombre.")
            modulo.nombre = req.nombre
        modulo.descripcion = req.descripcion
        modulo.ruta = req.ruta
        modulo.icono = req.icono

        return modulo_sistema_response(modulo)

    def eliminar_modulo(self, id_modulo: int) -> None:
        modulo = self.repo.find_by_id_and_estado_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        if self.repo.count_asignaciones_activas(modulo.id) > 0:
            raise BadRequestException(
                "No se puede desactivar el módulo porque tiene asignaciones activas."
            )
        modulo.estado = False

    def activar_modulo(self, id_modulo: int):
        modulo = self.repo.find_by_id(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        modulo.estado = True
        return modulo_sistema_response(modulo)