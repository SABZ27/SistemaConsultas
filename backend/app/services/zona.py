from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.models.enums import TipoEstructura
from app.models.sede import Sede
from app.models.zona import Zona
from app.repositories.recurso_fisico import RecursoFisicoRepository
from app.repositories.sede import SedeRepository
from app.repositories.zona import ZonaRepository
from app.schemas.zona import ZonaResponse


def _response(zona: Zona) -> ZonaResponse:
    return ZonaResponse(
        id=zona.id,
        sedeId=zona.sede_id,
        nombre=zona.nombre,
        estado=zona.estado,
    )


class ZonaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ZonaRepository(db)
        self.sede_repo = SedeRepository(db)
        self.recurso_repo = RecursoFisicoRepository(db)

    def registrar(self, req):
        sede = self._obtener_sede_activa(req.sedeId)
        self._validar_sede_admite_zonas(sede)
        if (
            self.repo.find_by_sede_and_nombre_and_estado_true(req.sedeId, req.nombre)
            is not None
        ):
            raise BadRequestException(
                "Ya existe una zona activa con ese nombre en la sede."
            )

        zona = Zona(sede_id=req.sedeId, nombre=req.nombre)
        self.repo.save(zona)
        return _response(zona)

    def listar_zonas(self, sede_id: int | None = None, incluir_inactivos: bool = False):
        if sede_id is None:
            zonas = self.repo.find_all(incluir_inactivos)
        else:
            zonas = self.repo.find_all_by_sede(sede_id, incluir_inactivos)
        return [_response(z) for z in zonas]

    def obtener_zona_por_id(self, id_zona: int):
        zona = self.repo.find_by_id_and_estado_true(id_zona)
        if zona is None:
            raise ResourceNotFoundException("Zona no encontrada.")
        return _response(zona)

    def actualizar_zona(self, id_zona: int, req):
        zona = self.repo.find_by_id_and_estado_true(id_zona)
        if zona is None:
            raise ResourceNotFoundException("Zona no encontrada.")

        sede = self._obtener_sede_activa(req.sedeId)
        self._validar_sede_admite_zonas(sede)

        if zona.sede_id != req.sedeId and self._tiene_recursos_activos(zona.id):
            raise BadRequestException(
                "No se puede cambiar la sede de la zona porque tiene recursos físicos activos."
            )

        if zona.nombre != req.nombre:
            existente = self.repo.find_by_sede_and_nombre_and_estado_true(
                req.sedeId, req.nombre
            )
            if existente is not None and existente.id != zona.id:
                raise BadRequestException(
                    "Ya existe una zona activa con ese nombre en la sede."
                )

        zona.sede_id = req.sedeId
        zona.nombre = req.nombre
        return _response(zona)

    def desactivar_zona(self, id_zona: int) -> None:
        zona = self.repo.find_by_id_and_estado_true(id_zona)
        if zona is None:
            raise ResourceNotFoundException("Zona no encontrada.")
        if self._tiene_recursos_activos(zona.id):
            raise BadRequestException(
                "No se puede desactivar la zona porque tiene recursos físicos activos."
            )
        zona.estado = False

    def activar_zona(self, id_zona: int):
        zona = self.repo.find_by_id(id_zona)
        if zona is None:
            raise ResourceNotFoundException("Zona no encontrada.")
        zona.estado = True
        return _response(zona)

    def _obtener_sede_activa(self, sede_id: int) -> Sede:
        sede = self.sede_repo.find_by_id_and_estado_true(sede_id)
        if sede is None:
            raise BadRequestException("La sede indicada no existe o está inactiva.")
        return sede

    def _validar_sede_admite_zonas(self, sede: Sede) -> None:
        if sede.tipo_estructura == TipoEstructura.SALONES:
            raise BadRequestException("Una sede de tipo SALONES no admite zonas.")

    def _tiene_recursos_activos(self, id_zona: int) -> bool:
        return self.recurso_repo.count_by_zona_and_estado_true(id_zona) > 0
