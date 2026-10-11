from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo
from app.db.session import get_db
from app.schemas.recurso_fisico import (
    RecursoFisicoResponse,
    RegistroRecursoFisicoRequest,
    UpdateRecursoFisicoRequest,
)
from app.services.recurso_fisico import RecursoFisicoService

NOMBRE_MODULO = "INFRAESTRUCTURA"

router = APIRouter(prefix="/recursos-fisicos", tags=["Recursos Físicos"])


@router.get("", response_model=list[RecursoFisicoResponse])
def listar_recursos(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return RecursoFisicoService(db).listar_recursos_fisicos()


@router.post("", response_model=RecursoFisicoResponse, status_code=status.HTTP_201_CREATED)
def crear_recurso(
    req: RegistroRecursoFisicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RecursoFisicoService(db).registrar_recurso_fisico(req)


@router.get("/{id_recurso}", response_model=RecursoFisicoResponse)
def obtener_recurso(
    id_recurso: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return RecursoFisicoService(db).obtener_recurso_fisico_por_id(id_recurso)


@router.put("/{id_recurso}", response_model=RecursoFisicoResponse)
def actualizar_recurso(
    id_recurso: int,
    req: UpdateRecursoFisicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return RecursoFisicoService(db).actualizar_recurso_fisico(id_recurso, req)


@router.delete("/{id_recurso}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_recurso(
    id_recurso: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    RecursoFisicoService(db).eliminar_recurso_fisico(id_recurso)