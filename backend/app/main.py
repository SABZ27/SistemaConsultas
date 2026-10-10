from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import (
    auth,
    bloques,
    comentarios,
    modulos,
    notificaciones,
    programas,
    recursos,
    sedes,
    solicitudes_consultas,
    usuarios,
)
from app.core.security import decode_token
from app.db.session import init_db
from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.exceptions.handlers import (
    bad_request_exception_handler,
    http_exception_handler,
    resource_not_found_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Sistema Consultas - API",
        description="API del sistema de gestión de consultas académicas (IUB).",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.repositories.usuario import UsuarioRepository
    from app.utils.seguridad import establecer_usuario_actual

    @app.middleware("http")
    async def _establecer_usuario_actual(_request, call_next):
        authorization = _request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
            correo = None
            try:
                correo = decode_token(token)
            except Exception:
                correo = None
            if correo:
                from app.db.session import SessionLocal

                db = SessionLocal()
                try:
                    usuario = UsuarioRepository(db).find_by_correo_and_activo_true(correo)
                finally:
                    db.close()
                if usuario is not None:
                    establecer_usuario_actual(usuario.correo)
        return await call_next(_request)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ResourceNotFoundException, resource_not_found_handler)
    app.add_exception_handler(BadRequestException, bad_request_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(auth.router)
    app.include_router(usuarios.router)
    app.include_router(programas.router)
    app.include_router(modulos.router)
    app.include_router(sedes.router)
    app.include_router(bloques.router)
    app.include_router(recursos.router)
    app.include_router(solicitudes_consultas.router)
    app.include_router(comentarios.router)
    app.include_router(notificaciones.router)

    return app


app = crear_app()