import datetime as dt

import bcrypt
import jwt

from app.core.config import settings


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


def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None