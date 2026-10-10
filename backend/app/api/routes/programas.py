from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.schemas.programa import (
    ProgAcademicoResponse,
    RegistroProgAcademicoRequest,
    UpdateProgAcademicoRequest,
)
from app.services.programa_academico import ProgramaAcademicoService

router = APIRouter(prefix="/programas", tags=["Programas Académicos"])


@router.get("", response_model=list[ProgAcademicoResponse])
def listar_programas(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user_optional),
):
    return ProgramaAcademicoService(db).listar_programas()


@router.post("", response_model=ProgAcademicoResponse, status_code=status.HTTP_201_CREATED)
def crear_programa(
    req: RegistroProgAcademicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ProgramaAcademicoService(db).registrar_programa(req)


@router.get("/{id_programa}", response_model=ProgAcademicoResponse)
def obtener_programa(
    id_programa: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ProgramaAcademicoService(db).obtener_programa_por_id(id_programa)


@router.put("/{id_programa}", response_model=ProgAcademicoResponse)
def actualizar_programa(
    id_programa: int,
    req: UpdateProgAcademicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ProgramaAcademicoService(db).actualizar_programa(id_programa, req)


@router.delete("/{id_programa}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_programa(
    id_programa: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    ProgramaAcademicoService(db).eliminar_programa(id_programa)