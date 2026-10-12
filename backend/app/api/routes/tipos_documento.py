from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo
from app.db.session import get_db
from app.schemas.tipo_documento import (
    RegistroTipoDocumentoRequest,
    TipoDocumentoResponse,
    UpdateTipoDocumentoRequest,
)
from app.services.tipo_documento import TipoDocumentoService

NOMBRE_MODULO = "TIPOS_DOCUMENTO"

router = APIRouter(prefix="/tipos-documento", tags=["Tipos de Documento"])


@router.get("", response_model=list[TipoDocumentoResponse])
def listar_tipos_documento(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return TipoDocumentoService(db).listar(incluir_inactivos)


@router.post("", response_model=TipoDocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo_documento(
    req: RegistroTipoDocumentoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return TipoDocumentoService(db).crear(req)


@router.get("/{id_tipo}", response_model=TipoDocumentoResponse)
def obtener_tipo_documento(
    id_tipo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return TipoDocumentoService(db).obtener_por_id(id_tipo)


@router.put("/{id_tipo}", response_model=TipoDocumentoResponse)
def actualizar_tipo_documento(
    id_tipo: int,
    req: UpdateTipoDocumentoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return TipoDocumentoService(db).actualizar(id_tipo, req)


@router.patch("/{id_tipo}/activar", response_model=TipoDocumentoResponse)
def activar_tipo_documento(
    id_tipo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return TipoDocumentoService(db).activar(id_tipo)


@router.delete("/{id_tipo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo_documento(
    id_tipo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    TipoDocumentoService(db).eliminar(id_tipo)
