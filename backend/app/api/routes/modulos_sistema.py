from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import requiere_modulo
from app.db.session import get_db
from app.schemas.modulo_sistema import (
    ModuloSistemaResponse,
    RegistroModuloSistemaRequest,
    UpdateModuloSistemaRequest,
)
from app.services.modulo_sistema import ModuloSistemaService

NOMBRE_MODULO = "ROLES_PERMISOS"

router = APIRouter(prefix="/modulos-sistema", tags=["Módulos del Sistema"])


@router.get("", response_model=list[ModuloSistemaResponse])
def listar_modulos_sistema(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ModuloSistemaService(db).listar_modulos(incluir_inactivos)


@router.post("", response_model=ModuloSistemaResponse, status_code=status.HTTP_201_CREATED)
def crear_modulo_sistema(
    req: RegistroModuloSistemaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ModuloSistemaService(db).crear_modulo(req)


@router.get("/{id_modulo}", response_model=ModuloSistemaResponse)
def obtener_modulo_sistema(
    id_modulo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ModuloSistemaService(db).obtener_modulo_por_id(id_modulo)


@router.put("/{id_modulo}", response_model=ModuloSistemaResponse)
def actualizar_modulo_sistema(
    id_modulo: int,
    req: UpdateModuloSistemaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ModuloSistemaService(db).actualizar_modulo(id_modulo, req)


@router.patch("/{id_modulo}/activar", response_model=ModuloSistemaResponse)
def activar_modulo_sistema(
    id_modulo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ModuloSistemaService(db).activar_modulo(id_modulo)


@router.delete("/{id_modulo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_modulo_sistema(
    id_modulo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    ModuloSistemaService(db).eliminar_modulo(id_modulo)