from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.calificacion import PromedioCalificacionesResponse
from app.services.calificacion_consulta import CalificacionConsultaService

router = APIRouter(prefix="/docentes", tags=["Calificaciones"])


@router.get("/{id_docente}/calificaciones/promedio", response_model=PromedioCalificacionesResponse)
def promedio_calificaciones(
    id_docente: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return CalificacionConsultaService(db).promedio_docente(id_docente)
