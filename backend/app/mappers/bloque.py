from app.models.bloque import Bloque
from app.schemas.bloque import BloqueResponse


def bloque_response(b: Bloque) -> BloqueResponse:
    return BloqueResponse(
        id=b.id,
        nombre=b.nombre,
        sedeId=b.sede_id,
        sedeNombre=b.sede.nombre,
        estado=b.estado,
    )