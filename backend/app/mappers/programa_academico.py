from app.models.programa_academico import ProgramaAcademico
from app.schemas.programa import ProgAcademicoResponse


def programa_academico_response(p: ProgramaAcademico) -> ProgAcademicoResponse:
    return ProgAcademicoResponse(id=p.id, nombre=p.nombre, activo=p.activo)