import datetime as dt
import hashlib
import secrets

import bcrypt
import jwt

from app.core.config import settings

# Rol del token interno (servicio a servicio). El microservicio Express exige
# este rol en POST /correos: solo el backend FastAPI puede pedir correos.
ROL_SERVICIO = "SERVICIO"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(correo: str, uid: int, rol: str, modulos: list[str]) -> str:
    ahora = dt.datetime.now(dt.timezone.utc)
    expiracion = ahora + dt.timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {
        "sub": correo,
        "uid": uid,
        "rol": rol,
        "modulos": modulos,
        "iat": ahora,
        "exp": expiracion,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    """Valida un token de usuario.

    Exige exp, sub, uid y rol; rechaza los tokens de servicio (rol SERVICIO o
    uid 0) para que no sirvan en endpoints de usuario.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "sub", "uid", "rol"]},
    )
    if payload.get("rol") == ROL_SERVICIO or payload.get("uid") == 0:
        raise jwt.InvalidTokenError("Token de servicio no válido para usuarios.")

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise jwt.InvalidTokenError("Token sin usuario.")
    return sub


def generar_token_reset() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_token_interno(minutos: int = 5) -> str:
    """Token de servicio a servicio (mismo JWT_SECRET que el microservicio).

    Se usa para las llamadas a Express que no son de un usuario (por ejemplo,
    el envío de correos). Vive muy poco tiempo: solo debe servir para la
    llamada en curso.
    """
    ahora = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": "servicios@sistema.local",
        "uid": 0,
        "rol": ROL_SERVICIO,
        "iat": ahora,
        "exp": ahora + dt.timedelta(minutes=minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
