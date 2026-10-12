from app.models.periodo_academico import PeriodoAcademico
from app.schemas.periodo import PeriodoResponse


def periodo_response(p: PeriodoAcademico) -> PeriodoResponse:
    return PeriodoResponse(
        id=p.id,
        nombre=p.nombre,
        fechaInicio=p.fecha_inicio,
        fechaFin=p.fecha_fin,
        estado=p.estado,
    )
