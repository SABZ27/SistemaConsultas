import unicodedata

from app.core.passwords_comunes import CONTRASENAS_COMUNES

LONGITUD_MINIMA = 10
LONGITUD_MAXIMA_BYTES = 72
LONGITUD_MINIMA_TERMINO = 4

MENSAJE_LONGITUD_MINIMA = "La contraseña debe tener al menos 10 caracteres"
MENSAJE_LONGITUD_MAXIMA = "La contraseña no puede superar los 72 bytes"
MENSAJE_ESPACIOS = "La contraseña no puede contener espacios"
MENSAJE_COMPOSICION = (
    "La contraseña debe incluir al menos una mayúscula, una minúscula, "
    "un número y un símbolo"
)
MENSAJE_COMUN = "La contraseña es demasiado común. Elige una diferente"
MENSAJE_DATOS_PERSONALES = (
    "La contraseña no puede contener el correo, el nombre, el apellido "
    "ni la identificación"
)


class PasswordPolicyError(ValueError):
    """Error de política que conserva el campo al que pertenece.

    Se lanza desde ``model_validator``; el manejador de validación usa
    ``campo`` para devolver el error en el formato por campo del proyecto.
    """

    def __init__(self, mensaje: str, campo: str = "password"):
        super().__init__(mensaje)
        self.campo = campo


def _normalizar(texto: str) -> str:
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto.lower())
        if not unicodedata.combining(caracter)
    )
    return "".join(caracter for caracter in sin_acentos if caracter.isalnum())


def validar_password(
    password: str,
    *,
    correo: str = "",
    nombre: str = "",
    apellido: str = "",
    identificacion: str = "",
) -> str | None:
    """Devuelve el primer incumplimiento de la política, o ``None``."""
    if len(password) < LONGITUD_MINIMA:
        return MENSAJE_LONGITUD_MINIMA
    if len(password.encode("utf-8")) > LONGITUD_MAXIMA_BYTES:
        return MENSAJE_LONGITUD_MAXIMA
    if any(caracter.isspace() for caracter in password):
        return MENSAJE_ESPACIOS
    if not any(caracter.isupper() for caracter in password):
        return MENSAJE_COMPOSICION
    if not any(caracter.islower() for caracter in password):
        return MENSAJE_COMPOSICION
    if not any(caracter.isdigit() for caracter in password):
        return MENSAJE_COMPOSICION
    if not any(
        not caracter.isalnum() and not caracter.isspace()
        for caracter in password
    ):
        return MENSAJE_COMPOSICION
    if password.lower() in CONTRASENAS_COMUNES:
        return MENSAJE_COMUN

    normalizada = _normalizar(password)
    terminos = [
        correo,
        correo.split("@")[0] if "@" in correo else "",
        nombre,
        apellido,
    ]
    for termino in terminos:
        for parte in str(termino).split():
            parte_normalizada = _normalizar(parte)
            if (
                len(parte_normalizada) >= LONGITUD_MINIMA_TERMINO
                and parte_normalizada in normalizada
            ):
                return MENSAJE_DATOS_PERSONALES

    identificacion_normalizada = _normalizar(str(identificacion))
    if identificacion_normalizada and identificacion_normalizada in normalizada:
        return MENSAJE_DATOS_PERSONALES

    return None


def validar_password_admin(
    password: str, *, correo: str = "", identificacion: str = ""
) -> str | None:
    if not password:
        return None
    return validar_password(
        password,
        correo=correo,
        nombre="Administrador",
        apellido="Sistema",
        identificacion=identificacion,
    )
