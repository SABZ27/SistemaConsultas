from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import obtener_ip
from app.db.session import get_db
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.schemas.auth import (
    CambiarPasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    ModuloInfo,
    ResetPasswordRequest,
)
from app.schemas.usuario import RegistroUsuarioRequest
from app.services.auth import AuthService
from app.services.email import EmailService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=MeResponse)
def mi_perfil(
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
) -> MeResponse:
    return AuthService(db).mi_perfil(usuario)


@router.get("/me/modulos", response_model=list[ModuloInfo])
def mis_modulos(
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
) -> list[ModuloInfo]:
    """Módulos del usuario autenticado, leídos de modulos_x_rol.

    No hay valores fijos: se consulta la tabla en cada petición, igual que
    /auth/me y que la autorización por módulos (requiere_modulo).
    """
    modulos = ModuloXRolRepository(db).activos_por_rol(usuario.rol_id)
    return [
        ModuloInfo(nombre=m.nombre, ruta=m.ruta, icono=m.icono)
        for m in modulos
    ]


@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    req: RegistroUsuarioRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    AuthService(db).registro(req, obtener_ip(request))
    return "Usuario registrado correctamente."


@router.post("/login", response_model=LoginResponse)
def iniciar_sesion(
    req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    return AuthService(db).login(req, obtener_ip(request))


@router.post("/forgot-password")
def olvidar_contrasenia(
    req: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    correo = AuthService(db).forgot_password(req, obtener_ip(request))
    if correo is not None:
        # El correo se envía en segundo plano (después del commit).
        background_tasks.add_task(EmailService().enviar, correo)
    return "Se ha generado un token de recuperación."


@router.post("/reset-password")
def restablecer_contrasenia(
    req: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    AuthService(db).reset_password(req, obtener_ip(request))
    return "Contraseña actualizada correctamente."


@router.post("/cambiar-password")
def cambiar_contrasenia(
    req: CambiarPasswordRequest,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
) -> str:
    AuthService(db).cambiar_password(usuario, req)
    return "Contraseña actualizada correctamente."