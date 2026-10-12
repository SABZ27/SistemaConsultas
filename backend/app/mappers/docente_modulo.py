from app.models.docente_modulo import DocenteModulo
from app.mappers.usuario import nombre_completo
from app.schemas.docente_modulo import DocenteModuloResponse


def docente_modulo_response(dm: DocenteModulo) -> DocenteModuloResponse:
    return DocenteModuloResponse(
        id=dm.id,
        docenteId=dm.docente_id,
        nombreDocente=nombre_completo(dm.docente),
        moduloId=dm.modulo_id,
        nombreModulo=dm.modulo.nombre,
        estado=dm.estado,
    )
