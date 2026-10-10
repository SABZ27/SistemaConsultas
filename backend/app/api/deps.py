from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository
from app.utils.seguridad import establecer_usuario_actual

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


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    correo = _correo_desde_credenciales(credenciales)
    usuario = None
    if correo:
        usuario = UsuarioRepository(db).find_by_correo_and_estado_true(correo)
    if usuario is None:
        raise HTTPException(status_code=401, detail="No se encontró una sesión activa.")
    establecer_usuario_actual(usuario.correo)
    return usuario


def get_current_user_optional(
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
    db: Session = Depends(get_db),
) -> Usuario | None:
    correo = _correo_desde_credenciales(credenciales)
    usuario = None
    if correo:
        usuario = UsuarioRepository(db).find_by_correo_and_estado_true(correo)
    if usuario is not None:
        establecer_usuario_actual(usuario.correo)
    return usuario


def admin_usuario(
    _usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    from app.models.enums import Rol

    if _usuario.rol != Rol.ADMINISTRADOR:
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden realizar esta acción.",
        )
    return _usuario