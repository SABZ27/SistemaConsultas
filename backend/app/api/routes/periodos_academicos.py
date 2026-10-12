from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo
from app.db.session import get_db
from app.schemas.periodo import (
    PeriodoResponse,
    RegistroPeriodoRequest,
    UpdatePeriodoRequest,
)
from app.services.periodo_academico import PeriodoAcademicoService

NOMBRE_MODULO = "PERIODOS_ACADEMICOS"

router = APIRouter(prefix="/periodos-academicos", tags=["Periodos Académicos"])


@router.get("", response_model=list[PeriodoResponse])
def listar_periodos(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return PeriodoAcademicoService(db).listar(incluir_inactivos)


@router.post("", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
def crear_periodo(
    req: RegistroPeriodoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return PeriodoAcademicoService(db).crear(req)


@router.get("/{id_periodo}", response_model=PeriodoResponse)
def obtener_periodo(
    id_periodo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return PeriodoAcademicoService(db).obtener_por_id(id_periodo)


@router.put("/{id_periodo}", response_model=PeriodoResponse)
def actualizar_periodo(
    id_periodo: int,
    req: UpdatePeriodoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return PeriodoAcademicoService(db).actualizar(id_periodo, req)


@router.patch("/{id_periodo}/activar", response_model=PeriodoResponse)
def activar_periodo(
    id_periodo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return PeriodoAcademicoService(db).activar(id_periodo)


@router.delete("/{id_periodo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_periodo(
    id_periodo: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    PeriodoAcademicoService(db).eliminar(id_periodo)
