from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_bearer_token, get_current_user
from app.db.session import get_db
from app.schemas.solicitud import (
    AsignarRecursoFisicoRequest,
    CambiarEstadoSolicitudRequest,
    ReasignarDocenteRequest,
    RegistroSolicitudConsultaRequest,
    SolicitudConsultaResponse,
    UpdateSolicitudConsultaRequest,
)
from app.services.email import CorreoPendiente, EmailService
from app.services.solicitud_consulta import SolicitudConsultaService

router = APIRouter(prefix="/solicitudes-consultas", tags=["Solicitudes de Consulta"])


def _programar_correos(
    background_tasks: BackgroundTasks,
    correos: list[CorreoPendiente],
) -> None:
    """Envía los correos en segundo plano.

    Los BackgroundTasks se ejecutan después de responder, es decir, después
    del commit de la transacción (get_db). Si el envío falla, el error se
    registra y el flujo principal no se rompe.
    """
    email_service = EmailService()
    for correo in correos:
        background_tasks.add_task(email_service.enviar, correo)


@router.get("", response_model=list[SolicitudConsultaResponse])
def listar_solicitudes(
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).listar_todas(usuario)


@router.post("", response_model=SolicitudConsultaResponse, status_code=status.HTTP_201_CREATED)
def registrar_solicitud(
    req: RegistroSolicitudConsultaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
    token: str = Depends(get_bearer_token),
):
    servicio = SolicitudConsultaService(db)
    respuesta = servicio.registrar(req, usuario, token)
    _programar_correos(background_tasks, servicio.correos_pendientes)
    return respuesta


@router.get("/{id_solicitud}", response_model=SolicitudConsultaResponse)
def obtener_solicitud(
    id_solicitud: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return SolicitudConsultaService(db).obtener_por_id(id_solicitud, usuario)


@router.put("/{id_solicitud}", response_model=SolicitudConsultaResponse)
def actualizar_solicitud(
    id_solicitud: int,
    req: UpdateSolicitudConsultaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
    token: str = Depends(get_bearer_token),
):
    servicio = SolicitudConsultaService(db)
    respuesta = servicio.actualizar(id_solicitud, req, usuario, token)
    _programar_correos(background_tasks, servicio.correos_pendientes)
    return respuesta


@router.patch("/{id_solicitud}/recurso-fisico", response_model=SolicitudConsultaResponse)
def asignar_recurso_fisico(
    id_solicitud: int,
    req: AsignarRecursoFisicoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    servicio = SolicitudConsultaService(db)
    respuesta = servicio.asignar_recurso_fisico(id_solicitud, req, usuario)
    _programar_correos(background_tasks, servicio.correos_pendientes)
    return respuesta


@router.patch("/{id_solicitud}/estado", response_model=SolicitudConsultaResponse)
def cambiar_estado(
    id_solicitud: int,
    req: CambiarEstadoSolicitudRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    servicio = SolicitudConsultaService(db)
    respuesta = servicio.cambiar_estado(id_solicitud, req, usuario)
    _programar_correos(background_tasks, servicio.correos_pendientes)
    return respuesta


@router.patch("/{id_solicitud}/docente", response_model=SolicitudConsultaResponse)
def reasignar_docente(
    id_solicitud: int,
    req: ReasignarDocenteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    servicio = SolicitudConsultaService(db)
    respuesta = servicio.reasignar_docente(id_solicitud, req, usuario)
    _programar_correos(background_tasks, servicio.correos_pendientes)
    return respuesta


@router.delete("/{id_solicitud}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_solicitud(
    id_solicitud: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    SolicitudConsultaService(db).eliminar(id_solicitud, usuario)


from app.schemas.calificacion import CalificacionRequest, CalificacionResponse
from app.services.calificacion_consulta import CalificacionConsultaService


@router.post("/{id_solicitud}/calificacion", response_model=CalificacionResponse, status_code=status.HTTP_201_CREATED)
def calificar_solicitud(
    id_solicitud: int,
    req: CalificacionRequest,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return CalificacionConsultaService(db).calificar(id_solicitud, req, usuario)


@router.get("/{id_solicitud}/calificacion", response_model=CalificacionResponse)
def obtener_calificacion(
    id_solicitud: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return CalificacionConsultaService(db).obtener_por_solicitud(id_solicitud, usuario)