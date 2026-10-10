from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.bloque import (
    BloqueResponse,
    RegistroBloqueRequest,
    UpdateBloqueRequest,
)
from app.services.bloque import BloqueService

router = APIRouter(prefix="/bloques", tags=["Bloques"])


@router.post("", response_model=BloqueResponse, status_code=status.HTTP_201_CREATED)
def crear_bloque(
    req: RegistroBloqueRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return BloqueService(db).registrar_bloque(req)


@router.get("", response_model=list[BloqueResponse])
def listar_bloques(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return BloqueService(db).listar_bloques()


@router.get("/{id_bloque}", response_model=BloqueResponse)
def obtener_bloque(
    id_bloque: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return BloqueService(db).obtener_bloque_por_id(id_bloque)


@router.put("/{id_bloque}", response_model=BloqueResponse)
def actualizar_bloque(
    id_bloque: int,
    req: UpdateBloqueRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return BloqueService(db).actualizar_bloque(id_bloque, req)


@router.delete("/{id_bloque}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_bloque(
    id_bloque: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    BloqueService(db).eliminar_bloque(id_bloque)