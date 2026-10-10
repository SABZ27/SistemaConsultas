from contextvars import ContextVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository

USUARIO_CORREO_VAR: ContextVar[str | None] = ContextVar("usuario_correo", default=None)


def establecer_usuario_actual(correo: str) -> None:
    USUARIO_CORREO_VAR.set(correo)


def obtener_correo() -> str:
    correo = USUARIO_CORREO_VAR.get()
    if not correo:
        raise HTTPException(status_code=401, detail="No se encontró una sesión activa.")
    return correo


def obtener_usuario_auth(db: Session) -> Usuario:
    correo = obtener_correo()
    usuario = UsuarioRepository(db).find_by_correo_and_activo_true(correo)
    if usuario is None:
        raise HTTPException(status_code=401, detail="No se encontró una sesión activa.")
    return usuario