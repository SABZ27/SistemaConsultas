from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.sede import RegistroSedeRequest, SedeResponse, UpdateSedeRequest
from app.services.sede import SedeService

router = APIRouter(prefix="/sedes", tags=["Sedes"])


@router.post("", response_model=SedeResponse, status_code=status.HTTP_201_CREATED)
def crear_sede(
    req: RegistroSedeRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SedeService(db).registrar_sede(req)


@router.get("", response_model=list[SedeResponse])
def listar_sedes(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SedeService(db).listar_sedes()


@router.get("/{id_sede}", response_model=SedeResponse)
def obtener_sede(
    id_sede: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SedeService(db).obtener_sede_por_id(id_sede)


@router.put("/{id_sede}", response_model=SedeResponse)
def actualizar_sede(
    id_sede: int,
    req: UpdateSedeRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SedeService(db).actualizar_sede(id_sede, req)


@router.delete("/{id_sede}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sede(
    id_sede: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    SedeService(db).eliminar_sede(id_sede)