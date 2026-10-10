from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.notificacion import NotificacionResponse
from app.services.notificacion import NotificacionService

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("", response_model=list[NotificacionResponse])
def listar_notificaciones(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return NotificacionService(db).listar_notificaciones()


@router.get("/no-leidas/count")
def contar_notificaciones_no_leidas(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
) -> int:
    return NotificacionService(db).contar_notificaciones_no_leidas()


@router.patch("/{id_notificacion}/leer", response_model=NotificacionResponse)
def marcar_como_leida(
    id_notificacion: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return NotificacionService(db).marcar_como_leida(id_notificacion)