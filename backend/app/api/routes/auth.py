from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    ResetPasswordRequest,
)
from app.schemas.usuario import RegistroUsuarioRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=MeResponse)
def mi_perfil(
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
) -> MeResponse:
    return AuthService(db).mi_perfil(usuario)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(req: RegistroUsuarioRequest, db: Session = Depends(get_db)) -> str:
    AuthService(db).registro(req)
    return "Usuario registrado correctamente."


@router.post("/login", response_model=LoginResponse)
def iniciar_sesion(req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    return AuthService(db).login(req)


@router.post("/forgot-password")
def olvidar_contrasenia(req: ForgotPasswordRequest, db: Session = Depends(get_db)) -> str:
    AuthService(db).forgot_password(req)
    return "Se ha generado un token de recuperación."


@router.post("/reset-password")
def restablecer_contrasenia(req: ResetPasswordRequest, db: Session = Depends(get_db)) -> str:
    AuthService(db).reset_password(req)
    return "Contraseña actualizada correctamente."