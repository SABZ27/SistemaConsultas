from app.models.modulo_sistema import ModuloSistema
from app.schemas.modulo_sistema import ModuloSistemaResponse


def modulo_sistema_response(m: ModuloSistema) -> ModuloSistemaResponse:
    return ModuloSistemaResponse(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        ruta=m.ruta,
        icono=m.icono,
        estado=m.estado,
    )