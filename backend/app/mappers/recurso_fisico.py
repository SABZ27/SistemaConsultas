from app.models.recurso_fisico import RecursoFisico
from app.schemas.recurso_fisico import RecursoFisicoResponse


def recurso_fisico_response(r: RecursoFisico) -> RecursoFisicoResponse:
    return RecursoFisicoResponse(
        id=r.id,
        nombre=r.nombre,
        bloqueId=r.bloque_id,
        bloqueNombre=r.bloque.nombre,
        tipo=r.tipo,
        activo=r.activo,
    )