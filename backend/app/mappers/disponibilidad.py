from app.mappers.usuario import nombre_completo
from app.models.disponibilidad_docente import DisponibilidadDocente
from app.schemas.disponibilidad import DisponibilidadResponse


def disponibilidad_response(d: DisponibilidadDocente) -> DisponibilidadResponse:
    return DisponibilidadResponse(
        id=d.id,
        docenteId=d.docente_id,
        nombreDocente=nombre_completo(d.docente),
        diaSemana=d.dia_semana,
        horaInicio=d.hora_inicio,
        horaFin=d.hora_fin,
        estado=d.estado,
    )
