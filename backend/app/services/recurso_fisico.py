from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.models.enums import TipoEstructura
from app.models.recurso_fisico import RecursoFisico
from app.models.sede import Sede
from app.models.zona import Zona
from app.repositories.recurso_fisico import RecursoFisicoRepository
from app.repositories.sede import SedeRepository
from app.repositories.zona import ZonaRepository
from app.schemas.recurso_fisico import RecursoFisicoResponse


def ubicacion_recurso(recurso: RecursoFisico) -> str:
    partes: list[str] = []
    if recurso.sede is not None:
        partes.append(recurso.sede.nombre)
    if recurso.zona is not None:
        partes.append(recurso.zona.nombre)
    partes.append(recurso.nombre)
    return " · ".join(partes)


def _response(recurso: RecursoFisico) -> RecursoFisicoResponse:
    return RecursoFisicoResponse(
        id=recurso.id,
        sedeId=recurso.sede_id,
        zonaId=recurso.zona_id,
        nombre=recurso.nombre,
        tipo=recurso.tipo,
        ubicacion=ubicacion_recurso(recurso),
        estado=recurso.estado,
    )


class RecursoFisicoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecursoFisicoRepository(db)
        self.sede_repo = SedeRepository(db)
        self.zona_repo = ZonaRepository(db)

    def registrar(self, req):
        sede, zona = self._validar_sede_y_zona(req.sedeId, req.zonaId)
        self._validar_unicidad(sede.id, zona.id if zona else None, req.nombre, None)

        recurso = RecursoFisico(
            sede_id=sede.id,
            zona_id=zona.id if zona else None,
            nombre=req.nombre,
            tipo=req.tipo,
        )
        self.repo.save(recurso)
        return _response(recurso)

    def listar_recursos(
        self,
        sede_id: int | None = None,
        zona_id: int | None = None,
        incluir_inactivos: bool = False,
    ):
        if zona_id is not None:
            recursos = self.repo.find_all_by_zona(zona_id, incluir_inactivos)
        elif sede_id is not None:
            recursos = self.repo.find_all_by_sede(sede_id, incluir_inactivos)
        else:
            recursos = self.repo.find_all(incluir_inactivos)
        return [_response(r) for r in recursos]

    def obtener_recurso_por_id(self, id_recurso: int):
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        return _response(recurso)

    def actualizar_recurso(self, id_recurso: int, req):
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")

        sede, zona = self._validar_sede_y_zona(req.sedeId, req.zonaId)
        self._validar_unicidad(sede.id, zona.id if zona else None, req.nombre, recurso.id)

        recurso.sede_id = sede.id
        recurso.zona_id = zona.id if zona else None
        recurso.nombre = req.nombre
        recurso.tipo = req.tipo
        return _response(recurso)

    def desactivar_recurso(self, id_recurso: int) -> None:
        recurso = self.repo.find_by_id_and_estado_true(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        recurso.estado = False

    def activar_recurso(self, id_recurso: int):
        recurso = self.repo.find_by_id(id_recurso)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        recurso.estado = True
        return _response(recurso)

    def _validar_sede_y_zona(
        self, sede_id: int, zona_id: int | None
    ) -> tuple[Sede, Zona | None]:
        sede = self.sede_repo.find_by_id_and_estado_true(sede_id)
        if sede is None:
            raise BadRequestException("La sede indicada no existe o está inactiva.")

        zona = None
        if zona_id is not None:
            zona = self.zona_repo.find_by_id_and_estado_true(zona_id)
            if zona is None:
                raise BadRequestException("La zona indicada no existe o está inactiva.")
            if zona.sede_id != sede.id:
                raise BadRequestException(
                    "La zona indicada no pertenece a la sede del recurso."
                )

        if sede.tipo_estructura == TipoEstructura.SALONES and zona is not None:
            raise BadRequestException(
                "Una sede de tipo SALONES no admite zonas en sus recursos."
            )

        if (
            sede.tipo_estructura in (TipoEstructura.BLOQUES, TipoEstructura.PISOS)
            and zona is None
        ):
            raise BadRequestException(
                "Debe indicar la zona del recurso para sedes de tipo BLOQUES o PISOS."
            )

        return sede, zona

    def _validar_unicidad(
        self, sede_id: int, zona_id: int | None, nombre: str, id_excluido: int | None
    ) -> None:
        existente = self.repo.find_by_sede_zona_nombre_and_estado_true(
            sede_id, zona_id, nombre
        )
        if existente is not None and existente.id != id_excluido:
            raise BadRequestException(
                "Ya existe un recurso físico activo con ese nombre en la sede o zona indicada."
            )
