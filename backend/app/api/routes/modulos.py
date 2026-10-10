from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.modulo import ModuloResponse, RegistroModuloRequest, UpdateModuloRequest
from app.services.modulo import ModuloService

router = APIRouter(prefix="/modulos", tags=["Módulos"])


@router.post("", response_model=ModuloResponse, status_code=status.HTTP_201_CREATED)
def crear_modulo(
    req: RegistroModuloRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ModuloService(db).registrar(req)


@router.get("", response_model=list[ModuloResponse])
def listar_modulos(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ModuloService(db).listar_modulos()


@router.get("/{id_modulo}", response_model=ModuloResponse)
def obtener_modulo(
    id_modulo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ModuloService(db).obtener_modulo_por_id(id_modulo)


@router.put("/{id_modulo}", response_model=ModuloResponse)
def actualizar_modulo(
    id_modulo: int,
    req: UpdateModuloRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ModuloService(db).actualizar_modulo(id_modulo, req)


@router.delete("/{id_modulo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_modulo(
    id_modulo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    ModuloService(db).eliminar_modulo(id_modulo)