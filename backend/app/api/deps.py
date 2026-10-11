from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.usuario import Usuario
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.usuario import UsuarioRepository

seguridad_bearer = HTTPBearer(auto_error=False)


def _correo_desde_credenciales(
    credenciales: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credenciales is None:
        return None
    try:
        return decode_token(credenciales.credentials)
    except Exception:
        return None


def _correo_de_request(request: Request) -> str | None:
    return getattr(request.state, "usuario_correo", None)


def _buscar_usuario(request: Request, credenciales, db: Session) -> Usuario | None:
    correo = _correo_de_request(request)
    if not correo and credenciales is not None:
        correo = _correo_desde_credenciales(credenciales)
    if not correo:
        return None
    return UsuarioRepository(db).find_by_correo_and_estado_true(correo)


def get_current_user(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = _buscar_usuario(request, credenciales, db)
    if usuario is None:
        raise HTTPException(status_code=401, detail="No se encontró una sesión activa.")
    return usuario


def get_current_user_optional(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
    db: Session = Depends(get_db),
) -> Usuario | None:
    return _buscar_usuario(request, credenciales, db)


def requiere_modulo(nombre_modulo: str):
    def _dependencia(
        usuario: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if not ModuloXRolRepository(db).existe_permiso_activo(usuario.rol_id, nombre_modulo):
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para realizar esta acción.",
            )
        return usuario

    return _dependencia