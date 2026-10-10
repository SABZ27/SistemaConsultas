import logging
from datetime import datetime

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.schemas.mensajes import etiqueta_campo

logger = logging.getLogger("sistema_consultas")

NOMBRE_ERROR = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _cuerpo(status: int, message: str, errors: dict | None = None) -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "error": NOMBRE_ERROR.get(status, "Error"),
        "message": message,
        "errors": errors,
    }


def _mensaje_longitud(campo: str, tipo: str, ctx: dict) -> str:
    etiqueta = etiqueta_campo(campo)
    min_l = ctx.get("min_length")
    max_l = ctx.get("max_length")

    if tipo == "string_too_long":
        return f"{etiqueta} no puede superar los {max_l} caracteres"

    if min_l == 1:
        if campo == "descripcion":
            return "La descripción no puede estar vacía"
        if campo == "contenido":
            return "El comentario debe tener contenido."
        if campo == "correo":
            return "El correo es obligatorio"
        if campo == "token":
            return "El token es obligatorio"
        return f"{etiqueta} no puede estar vacío"

    if min_l is not None and max_l is not None:
        return f"{etiqueta} debe tener entre {min_l} y {max_l} caracteres"
    if min_l is not None:
        return f"{etiqueta} debe tener al menos {min_l} caracteres"
    return f"{etiqueta} no puede superar los {max_l} caracteres"


def _traducir_errores(exc: RequestValidationError) -> dict[str, str]:
    errores: dict[str, str] = {}
    for e in exc.errors():
        loc = [str(p) for p in e["loc"] if p not in ("body", "query", "path", "json")]
        campo = ".".join(loc) if loc else "cuerpo"
        tipo = e["type"]
        ctx = e.get("ctx") or {}

        if tipo == "missing":
            mensaje = f"{etiqueta_campo(campo)} es obligatorio"
        elif tipo in ("string_too_short", "string_too_long"):
            mensaje = _mensaje_longitud(campo, tipo, ctx)
        elif tipo == "value_error":
            err = ctx.get("error")
            mensaje = str(err) if err else "Valor inválido."
        elif tipo in ("literal_error", "enum"):
            mensaje = f"{etiqueta_campo(campo)} no es un valor válido. Valores permitidos: {ctx.get('expected', 'consulta la documentación')}"
        elif tipo in ("int_parsing", "int_type", "int_cast_error"):
            mensaje = f"{etiqueta_campo(campo)} debe ser un número."
        elif tipo.startswith("date"):
            mensaje = f"{etiqueta_campo(campo)} debe tener un formato de fecha válido (AAAA-MM-DD)."
        elif tipo.startswith("time"):
            mensaje = f"{etiqueta_campo(campo)} debe tener un formato de hora válido (HH:MM)."
        elif tipo == "len_less_than_equal":
            mensaje = f"{etiqueta_campo(campo)} no puede tener más de {ctx.get('max_length', '')} caracteres"
        elif tipo.startswith("string"):
            mensaje = f"{etiqueta_campo(campo)} debe ser un texto."
        elif tipo == "bool_parsing":
            mensaje = f"{etiqueta_campo(campo)} debe ser verdadero o falso."
        else:
            mensaje = e.get("msg", "Valor inválido.")

        errores[campo] = mensaje
    return errores


def validation_exception_handler(_request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=_cuerpo(400, "Error de validación.", errors=_traducir_errores(exc)),
    )


def resource_not_found_handler(_request, exc: ResourceNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=_cuerpo(404, exc.message or "Recurso no encontrado."),
    )


def bad_request_exception_handler(_request, exc: BadRequestException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=_cuerpo(400, exc.message or "Solicitud inválida."),
    )


def http_exception_handler(_request, exc: StarletteHTTPException) -> JSONResponse:
    detalle = exc.detail
    mensaje = detalle if isinstance(detalle, str) else "Ocurrió un error."
    return JSONResponse(
        status_code=exc.status_code,
        content=_cuerpo(exc.status_code, mensaje),
    )


def unhandled_exception_handler(_request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado.", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=_cuerpo(500, "Error interno del servidor."),
    )