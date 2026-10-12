from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo
from app.db.session import get_db
from app.schemas.disponibilidad import (
    DisponibilidadResponse,
    RegistroDisponibilidadRequest,
    UpdateDisponibilidadRequest,
)
from app.services.disponibilidad_docente import DisponibilidadDocenteService

NOMBRE_MODULO = "DISPONIBILIDAD_DOCENTE"

router = APIRouter(prefix="/disponibilidad-docente", tags=["Disponibilidad Docente"])


@router.get("", response_model=list[DisponibilidadResponse])
def listar_disponibilidad(
    docenteId: int | None = Query(default=None),
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return DisponibilidadDocenteService(db).listar(docenteId, incluir_inactivos)


@router.post("", response_model=DisponibilidadResponse, status_code=status.HTTP_201_CREATED)
def crear_disponibilidad(
    req: RegistroDisponibilidadRequest,
    db: Session = Depends(get_db),
    usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DisponibilidadDocenteService(db).crear(req, usuario)


@router.get("/{id_disponibilidad}", response_model=DisponibilidadResponse)
def obtener_disponibilidad(
    id_disponibilidad: int,
    db: Session = Depends(get_db),
    usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DisponibilidadDocenteService(db).obtener_por_id(id_disponibilidad, usuario)


@router.put("/{id_disponibilidad}", response_model=DisponibilidadResponse)
def actualizar_disponibilidad(
    id_disponibilidad: int,
    req: UpdateDisponibilidadRequest,
    db: Session = Depends(get_db),
    usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DisponibilidadDocenteService(db).actualizar(id_disponibilidad, req, usuario)


@router.patch("/{id_disponibilidad}/activar", response_model=DisponibilidadResponse)
def activar_disponibilidad(
    id_disponibilidad: int,
    db: Session = Depends(get_db),
    usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DisponibilidadDocenteService(db).activar(id_disponibilidad, usuario)


@router.delete("/{id_disponibilidad}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_disponibilidad(
    id_disponibilidad: int,
    db: Session = Depends(get_db),
    usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    DisponibilidadDocenteService(db).eliminar(id_disponibilidad, usuario)
