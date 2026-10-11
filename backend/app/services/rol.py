from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.rol import modulo_asignacion_response, rol_response
from app.models.modulo_x_rol import ModuloXRol
from app.models.rol import Rol
from app.repositories.modulo_sistema import ModuloSistemaRepository
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.rol import RolRepository
from app.schemas.rol import RegistroRolRequest, UpdateRolRequest


class RolService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RolRepository(db)
        self.mxl_repo = ModuloXRolRepository(db)
        self.modulo_repo = ModuloSistemaRepository(db)

    def listar_roles(self, incluir_inactivos: bool = False):
        filas = self.repo.find_all() if incluir_inactivos else self.repo.find_all_by_estado_true()
        return [rol_response(r) for r in filas]

    def crear_rol(self, req: RegistroRolRequest):
        rol_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
        if rol_existente is not None:
            raise BadRequestException("Ya existe un rol con ese nombre.")
        rol = Rol(nombre=req.nombre, descripcion=req.descripcion)
        self.repo.save(rol)
        return rol_response(rol)

    def obtener_rol_por_id(self, id_rol: int):
        rol = self.repo.find_by_id_and_estado_true(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")
        return rol_response(rol)

    def actualizar_rol(self, id_rol: int, req: UpdateRolRequest):
        rol = self.repo.find_by_id_and_estado_true(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")

        if rol.nombre != req.nombre:
            rol_existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if rol_existente is not None and rol_existente.id != rol.id:
                raise BadRequestException("Ya existe un rol con ese nombre.")
            rol.nombre = req.nombre
        rol.descripcion = req.descripcion

        return rol_response(rol)

    def eliminar_rol(self, id_rol: int) -> None:
        rol = self.repo.find_by_id_and_estado_true(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")
        if self.repo.count_usuarios_activos(rol.id) > 0:
            raise BadRequestException(
                "No se puede desactivar el rol porque tiene usuarios activos."
            )
        rol.estado = False

    def activar_rol(self, id_rol: int):
        rol = self.repo.find_by_id(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")
        rol.estado = True
        return rol_response(rol)

    def obtener_modulos(self, id_rol: int):
        rol = self.repo.find_by_id_and_estado_true(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")
        return [
            modulo_asignacion_response(m)
            for m in self.mxl_repo.activos_por_rol(rol.id)
        ]

    def reemplazar_modulos(self, id_rol: int, modulo_ids: list[int]):
        rol = self.repo.find_by_id_and_estado_true(id_rol)
        if rol is None:
            raise ResourceNotFoundException("Rol no encontrado.")

        nuevos = set(modulo_ids)
        for id_modulo in nuevos:
            if self.modulo_repo.find_by_id_and_estado_true(id_modulo) is None:
                raise BadRequestException("Módulo no encontrado.")

        activos = self.mxl_repo.find_by_rol_id_and_estado_true(rol.id)
        actuales = {mxr.modulo_id for mxr in activos}

        for id_modulo in nuevos - actuales:
            par = self.mxl_repo.find_by_rol_and_modulo(rol.id, id_modulo)
            if par is None:
                self.mxl_repo.save(ModuloXRol(rol_id=rol.id, modulo_id=id_modulo))
            else:
                par.estado = True

        for mxr in activos:
            if mxr.modulo_id not in nuevos:
                mxr.estado = False

        self.db.flush()
        return self.obtener_modulos(rol.id)