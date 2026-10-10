from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.schemas.solicitud import (
    AsignarRecursoFisicoRequest,
    CambiarEstadoSolicitudRequest,
    ReasignarDocenteRequest,
    RegistroSolicitudConsultaRequest,
    SolicitudConsultaResponse,
    UpdateSolicitudConsultaRequest,
)
from app.services.solicitud_consulta import SolicitudConsultaService

router = APIRouter(prefix="/solicitudes-consultas", tags=["Solicitudes de Consulta"])


@router.get("", response_model=list[SolicitudConsultaResponse])
def listar_solicitudes(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user_optional),
):
    return SolicitudConsultaService(db).listar_todas()


@router.post("", response_model=SolicitudConsultaResponse, status_code=status.HTTP_201_CREATED)
def registrar_solicitud(
    req: RegistroSolicitudConsultaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).registrar(req)


@router.get("/{id_solicitud}", response_model=SolicitudConsultaResponse)
def obtener_solicitud(
    id_solicitud: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).obtener_por_id(id_solicitud)


@router.put("/{id_solicitud}", response_model=SolicitudConsultaResponse)
def actualizar_solicitud(
    id_solicitud: int,
    req: UpdateSolicitudConsultaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).actualizar(id_solicitud, req)


@router.patch("/{id_solicitud}/recurso-fisico", response_model=SolicitudConsultaResponse)
def asignar_recurso_fisico(
    id_solicitud: int,
    req: AsignarRecursoFisicoRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).asignar_recurso_fisico(id_solicitud, req)


@router.patch("/{id_solicitud}/estado", response_model=SolicitudConsultaResponse)
def cambiar_estado(
    id_solicitud: int,
    req: CambiarEstadoSolicitudRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).cambiar_estado(id_solicitud, req)


@router.patch("/{id_solicitud}/docente", response_model=SolicitudConsultaResponse)
def reasignar_docente(
    id_solicitud: int,
    req: ReasignarDocenteRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).reasignar_docente(id_solicitud, req)