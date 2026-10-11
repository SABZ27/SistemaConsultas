from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import requiere_modulo
from app.db.session import get_db
from app.schemas.rol import (
    AsignarModulosRequest,
    ModuloAsignacionResponse,
    RegistroRolRequest,
    RolResponse,
    UpdateRolRequest,
)
from app.services.rol import RolService

NOMBRE_MODULO = "ROLES_PERMISOS"

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RolResponse])
def listar_roles(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).listar_roles(incluir_inactivos)


@router.post("", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(
    req: RegistroRolRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).crear_rol(req)


@router.get("/{id_rol}", response_model=RolResponse)
def obtener_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).obtener_rol_por_id(id_rol)


@router.get("/{id_rol}/modulos", response_model=list[ModuloAsignacionResponse])
def obtener_modulos_de_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).obtener_modulos(id_rol)


@router.put("/{id_rol}/modulos", response_model=list[ModuloAsignacionResponse])
def reemplazar_modulos_de_rol(
    id_rol: int,
    req: AsignarModulosRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).reemplazar_modulos(id_rol, req.moduloIds)


@router.put("/{id_rol}", response_model=RolResponse)
def actualizar_rol(
    id_rol: int,
    req: UpdateRolRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).actualizar_rol(id_rol, req)


@router.patch("/{id_rol}/activar", response_model=RolResponse)
def activar_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RolService(db).activar_rol(id_rol)


@router.delete("/{id_rol}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    RolService(db).eliminar_rol(id_rol)