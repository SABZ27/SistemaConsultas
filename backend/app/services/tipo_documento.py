from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.tipo_documento import tipo_documento_response
from app.models.tipo_documento import TipoDocumento
from app.repositories.tipo_documento import TipoDocumentoRepository
from app.schemas.tipo_documento import (
    RegistroTipoDocumentoRequest,
    UpdateTipoDocumentoRequest,
)


class TipoDocumentoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TipoDocumentoRepository(db)

    def listar(self, incluir_inactivos: bool = False):
        filas = (
            self.repo.find_all()
            if incluir_inactivos
            else self.repo.find_all_by_estado_true()
        )
        return [tipo_documento_response(t) for t in filas]

    def crear(self, req: RegistroTipoDocumentoRequest):
        if self.repo.find_by_nombre_and_estado_true(req.nombre) is not None:
            raise BadRequestException("Ya existe un tipo de documento con ese nombre.")
        if self.repo.find_by_sigla_and_estado_true(req.sigla) is not None:
            raise BadRequestException("Ya existe un tipo de documento con esa sigla.")
        tipo = TipoDocumento(nombre=req.nombre, sigla=req.sigla)
        self.repo.save(tipo)
        return tipo_documento_response(tipo)

    def obtener_por_id(self, id_: int):
        tipo = self.repo.find_by_id_and_estado_true(id_)
        if tipo is None:
            raise ResourceNotFoundException("Tipo de documento no encontrado.")
        return tipo_documento_response(tipo)

    def actualizar(self, id_: int, req: UpdateTipoDocumentoRequest):
        tipo = self.repo.find_by_id_and_estado_true(id_)
        if tipo is None:
            raise ResourceNotFoundException("Tipo de documento no encontrado.")

        if tipo.nombre != req.nombre:
            existente = self.repo.find_by_nombre_and_estado_true(req.nombre)
            if existente is not None and existente.id != tipo.id:
                raise BadRequestException("Ya existe un tipo de documento con ese nombre.")
        if tipo.sigla != req.sigla:
            existente = self.repo.find_by_sigla_and_estado_true(req.sigla)
            if existente is not None and existente.id != tipo.id:
                raise BadRequestException("Ya existe un tipo de documento con esa sigla.")

        tipo.nombre = req.nombre
        tipo.sigla = req.sigla
        return tipo_documento_response(tipo)

    def eliminar(self, id_: int) -> None:
        tipo = self.repo.find_by_id_and_estado_true(id_)
        if tipo is None:
            raise ResourceNotFoundException("Tipo de documento no encontrado.")
        tipo.estado = False

    def activar(self, id_: int):
        tipo = self.repo.find_by_id(id_)
        if tipo is None:
            raise ResourceNotFoundException("Tipo de documento no encontrado.")
        tipo.estado = True
        return tipo_documento_response(tipo)
