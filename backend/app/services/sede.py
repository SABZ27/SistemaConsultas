from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.models.sede import Sede
from app.repositories.recurso_fisico import RecursoFisicoRepository
from app.repositories.sede import SedeRepository
from app.repositories.zona import ZonaRepository
from app.schemas.sede import SedeResponse


def _response(sede: Sede) -> SedeResponse:
    return SedeResponse(
        id=sede.id,
        nombre=sede.nombre,
        tipoEstructura=sede.tipo_estructura,
        estado=sede.estado,
    )


class SedeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SedeRepository(db)
        self.zona_repo = ZonaRepository(db)
        self.recurso_repo = RecursoFisicoRepository(db)

    def registrar(self, req):
        if self.repo.find_by_nombre_and_estado_true(req.nombre) is not None:
            raise BadRequestException("Ya existe una sede activa con ese nombre.")

        sede = Sede(nombre=req.nombre, tipo_estructura=req.tipoEstructura)
        self.repo.save(sede)
        return _response(sede)

    def listar_sedes(self, incluir_inactivos: bool = False):
        return [_response(s) for s in self.repo.find_all(incluir_inactivos)]

    def obtener_sede_por_id(self, id_sede: int):
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")
        return _response(sede)

    def actualizar_sede(self, id_sede: int, req):
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")

        if sede.nombre != req.nombre:
            existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if existente is not None and existente.id != sede.id:
                raise BadRequestException("Ya existe una sede activa con ese nombre.")

        if sede.tipo_estructura != req.tipoEstructura and self._tiene_hijos_activos(sede.id):
            raise BadRequestException(
                "No se puede cambiar el tipo de estructura de la sede porque tiene "
                "zonas o recursos físicos activos."
            )

        sede.nombre = req.nombre
        sede.tipo_estructura = req.tipoEstructura
        return _response(sede)

    def desactivar_sede(self, id_sede: int) -> None:
        sede = self.repo.find_by_id_and_estado_true(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")
        if self._tiene_hijos_activos(sede.id):
            raise BadRequestException(
                "No se puede desactivar la sede porque tiene zonas o recursos físicos activos."
            )
        sede.estado = False

    def activar_sede(self, id_sede: int):
        sede = self.repo.find_by_id(id_sede)
        if sede is None:
            raise ResourceNotFoundException("Sede no encontrada.")
        sede.estado = True
        return _response(sede)

    def _tiene_hijos_activos(self, id_sede: int) -> bool:
        if self.zona_repo.count_by_sede_and_estado_true(id_sede) > 0:
            return True
        return self.recurso_repo.count_by_sede_and_estado_true(id_sede) > 0
