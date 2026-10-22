from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo, tiene_permiso_modulo
from app.db.session import get_db
from app.schemas.recurso_fisico import (
    RecursoFisicoResponse,
    RegistroRecursoFisicoRequest,
    UpdateRecursoFisicoRequest,
)
from app.services.recurso_fisico import RecursoFisicoService

NOMBRE_MODULO = "INFRAESTRUCTURA"

router = APIRouter(prefix="/recursos-fisicos", tags=["Recursos físicos"])


def _exigir_infraestructura(db: Session, usuario, incluir_inactivos: bool) -> None:
    if incluir_inactivos and not tiene_permiso_modulo(db, usuario, NOMBRE_MODULO):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para realizar esta acción.",
        )


@router.get("", response_model=list[RecursoFisicoResponse])
def listar_recursos(
    sedeId: int | None = None,
    zonaId: int | None = None,
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    return RecursoFisicoService(db).listar_recursos(sedeId, zonaId, incluirInactivos)


@router.post("", response_model=RecursoFisicoResponse, status_code=status.HTTP_201_CREATED)
def crear_recurso(
    req: RegistroRecursoFisicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RecursoFisicoService(db).registrar(req)


@router.get("/{id_recurso}", response_model=RecursoFisicoResponse)
def obtener_recurso(
    id_recurso: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return RecursoFisicoService(db).obtener_recurso_por_id(id_recurso)


@router.put("/{id_recurso}", response_model=RecursoFisicoResponse)
def actualizar_recurso(
    id_recurso: int,
    req: UpdateRecursoFisicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RecursoFisicoService(db).actualizar_recurso(id_recurso, req)


@router.delete("/{id_recurso}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_recurso(
    id_recurso: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    RecursoFisicoService(db).desactivar_recurso(id_recurso)


@router.patch("/{id_recurso}/activar", response_model=RecursoFisicoResponse)
def activar_recurso(
    id_recurso: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RecursoFisicoService(db).activar_recurso(id_recurso)
