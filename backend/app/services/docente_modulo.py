from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.docente_modulo import docente_modulo_response
from app.models.docente_modulo import DocenteModulo
from app.models.enums import Rol
from app.repositories.docente_modulo import DocenteModuloRepository
from app.repositories.modulo import ModuloRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.docente_modulo import AsignarDocenteModuloRequest, DocenteResumenModulo


class DocenteModuloService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocenteModuloRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.modulo_repo = ModuloRepository(db)

    def listar(self, incluir_inactivos: bool = False):
        filas = (
            self.repo.find_all()
            if incluir_inactivos
            else self.repo.find_all_by_estado_true()
        )
        return [docente_modulo_response(dm) for dm in filas]

    def asignar(self, req: AsignarDocenteModuloRequest):
        docente = self.user_repo.find_by_id_and_estado_true(req.docenteId)
        if docente is None:
            raise ResourceNotFoundException("Docente no encontrado.")
        if docente.rol != Rol.DOCENTE:
            raise BadRequestException("El usuario indicado no tiene el rol DOCENTE.")

        modulo = self.modulo_repo.find_by_id_and_estado_true(req.moduloId)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")

        existente = self.repo.find_by_docente_and_modulo(docente.id, modulo.id)
        if existente is not None:
            if existente.estado:
                raise BadRequestException("El docente ya está asignado a ese módulo.")
            existente.estado = True
            return docente_modulo_response(existente)

        asignacion = DocenteModulo(docente_id=docente.id, modulo_id=modulo.id)
        self.repo.save(asignacion)
        return docente_modulo_response(asignacion)

    def obtener_por_id(self, id_: int):
        asignacion = self.repo.find_by_id_and_estado_true(id_)
        if asignacion is None:
            raise ResourceNotFoundException("Asignación docente-módulo no encontrada.")
        return docente_modulo_response(asignacion)

    def eliminar(self, id_: int) -> None:
        asignacion = self.repo.find_by_id_and_estado_true(id_)
        if asignacion is None:
            raise ResourceNotFoundException("Asignación docente-módulo no encontrada.")
        asignacion.estado = False

    def activar(self, id_: int):
        asignacion = self.repo.find_by_id(id_)
        if asignacion is None:
            raise ResourceNotFoundException("Asignación docente-módulo no encontrada.")
        asignacion.estado = True
        return docente_modulo_response(asignacion)

    def listar_docentes_por_modulo(self, id_modulo: int):
        modulo = self.modulo_repo.find_by_id_and_estado_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        return [
            DocenteResumenModulo(
                id=dm.docente.id, nombre=dm.docente.nombre, apellido=dm.docente.apellido
            )
            for dm in self.repo.find_all_by_modulo_id_and_estado_true(modulo.id)
        ]
