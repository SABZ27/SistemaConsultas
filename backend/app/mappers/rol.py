from app.models.modulo_sistema import ModuloSistema
from app.models.rol import Rol
from app.schemas.rol import ModuloAsignacionResponse, RolResponse


def rol_response(r: Rol) -> RolResponse:
    return RolResponse(id=r.id, nombre=r.nombre, descripcion=r.descripcion, estado=r.estado)


def modulo_asignacion_response(m: ModuloSistema) -> ModuloAsignacionResponse:
    return ModuloAsignacionResponse(id=m.id, nombre=m.nombre, ruta=m.ruta, icono=m.icono)