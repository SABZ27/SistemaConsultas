from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import (
    auth,
    calificaciones,
    comentarios,
    disponibilidad_docente,
    docentes_modulos,
    modulos,
    modulos_sistema,
    notificaciones,
    periodos_academicos,
    programas,
    recursos_fisicos,
    roles,
    sedes,
    solicitudes_consultas,
    tipos_documento,
    usuarios,
    zonas,
)
from app.core.config import origenes_cors, settings, validar_jwt_secret
from app.core.limite_cuerpo import MAX_CUERPO_BYTES, LimiteCuerpoMiddleware
from app.core.security import decode_token
from app.db.session import init_db
from app.exceptions.errors import (
    BadRequestException,
    ResourceNotFoundException,
    ServiceUnavailableException,
    TooManyRequestsException,
)
from app.exceptions.handlers import (
    bad_request_exception_handler,
    http_exception_handler,
    resource_not_found_handler,
    service_unavailable_handler,
    too_many_requests_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def crear_app() -> FastAPI:
    validar_jwt_secret(settings.jwt_secret)
    origenes = origenes_cors(settings.cors_origins)

    app = FastAPI(
        title="Sistema Consultas - API",
        description="API del sistema de gestión de consultas académicas (IUB).",
        version="1.0.0",
        lifespan=lifespan,
    )

    # El límite de cuerpo va dentro de CORS para que el 413 conserve sus
    # cabeceras; las cabeceras de seguridad envuelven a ambos.
    app.add_middleware(LimiteCuerpoMiddleware, max_bytes=MAX_CUERPO_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def _inyectar_correo_autenticado(_request, call_next):
        authorization = _request.headers.get("authorization", "")
        correo = None
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
            try:
                correo = decode_token(token)
            except Exception:
                correo = None
        _request.state.usuario_correo = correo
        return await call_next(_request)

    @app.middleware("http")
    async def _cabeceras_seguridad(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        proto = request.headers.get("x-forwarded-proto", "")
        proto = proto.split(",")[0].strip().lower()
        if request.url.scheme == "https" or proto == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ResourceNotFoundException, resource_not_found_handler)
    app.add_exception_handler(BadRequestException, bad_request_exception_handler)
    app.add_exception_handler(ServiceUnavailableException, service_unavailable_handler)
    app.add_exception_handler(TooManyRequestsException, too_many_requests_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(auth.router)
    app.include_router(usuarios.router)
    app.include_router(roles.router)
    app.include_router(modulos_sistema.router)
    app.include_router(programas.router)
    app.include_router(modulos.router)
    app.include_router(solicitudes_consultas.router)
    app.include_router(comentarios.router)
    app.include_router(notificaciones.router)
    app.include_router(docentes_modulos.router)
    app.include_router(tipos_documento.router)
    app.include_router(periodos_academicos.router)
    app.include_router(disponibilidad_docente.router)
    app.include_router(calificaciones.router)
    app.include_router(sedes.router)
    app.include_router(zonas.router)
    app.include_router(recursos_fisicos.router)

    return app


app = crear_app()