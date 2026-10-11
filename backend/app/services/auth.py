import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException

from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.errors import BadRequestException
from app.mappers.usuario import nombre_completo
from app.models.enums import Rol
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.password_reset_token import PasswordResetTokenRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    ModuloInfo,
    ResetPasswordRequest,
)
from app.schemas.usuario import RegistroUsuarioRequest
from app.services.email import EmailService
from app.services.usuario import UsuarioService


class AuthService:
    def __init__(self, db):
        self.db = db
        self.user_repo = UsuarioRepository(db)
        self.mxl_repo = ModuloXRolRepository(db)
        self.token_repo = PasswordResetTokenRepository(db)
        self.email_service = EmailService()
        self.usuario_service = UsuarioService(db)

    def login(self, req: LoginRequest) -> LoginResponse:
        usuario = self.user_repo.find_by_correo_and_estado_true(req.correo)
        if usuario is None or not verify_password(req.password, usuario.password):
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
        modulos = self.mxl_repo.activos_por_rol(usuario.rol_id)
        nombres_modulos = [m.nombre for m in modulos]
        token = create_access_token(usuario.correo, usuario.id, usuario.rol.value, nombres_modulos)
        return LoginResponse(
            token=token,
            id_usuario=usuario.id,
            correo=usuario.correo,
            nombre=nombre_completo(usuario),
            rol=usuario.rol,
            modulos=[
                ModuloInfo(nombre=m.nombre, ruta=m.ruta, icono=m.icono)
                for m in modulos
            ],
        )

    def mi_perfil(self, usuario: "Usuario") -> MeResponse:
        modulos = self.mxl_repo.activos_por_rol(usuario.rol_id)
        return MeResponse(
            id=usuario.id,
            identificacion=usuario.identificacion,
            correo=usuario.correo,
            nombre=nombre_completo(usuario),
            rol=usuario.rol,
            modulos=[
                ModuloInfo(nombre=m.nombre, ruta=m.ruta, icono=m.icono)
                for m in modulos
            ],
        )

    def registro(self, req: RegistroUsuarioRequest) -> None:
        if req.rol == Rol.ADMINISTRADOR:
            raise HTTPException(
                status_code=403,
                detail="El registro no permite crear usuarios con rol ADMINISTRADOR.",
            )
        self.usuario_service.crear_usuario(req)

    def forgot_password(self, req: ForgotPasswordRequest) -> None:
        usuario = self.user_repo.find_by_correo_and_estado_true(req.correo)
        if usuario is None:
            raise BadRequestException("No existe un usuario registrado con ese correo.")

        self.token_repo.delete_by_usuario_id(usuario.id)
        token = uuid.uuid4().__str__()
        self.token_repo.save(
            PasswordResetToken(
                token=token,
                usuario=usuario,
                fecha_expiracion=datetime.now() + timedelta(minutes=30),
                utilizado=False,
            )
        )
        self.email_service.enviar(
            para=usuario.correo,
            asunto="Recuperación de contraseña",
            contenido=(
                f"Hola {usuario.nombre},\n\n"
                "Has solicitado recuperar tu contraseña.\n\n"
                "Utiliza el siguiente token para restablecerla:\n\n"
                f"{token}\n\n"
                "Este token expira en 30 minutos."
            ),
        )

    def reset_password(self, req: ResetPasswordRequest) -> None:
        password_reset_token = self.token_repo.find_by_token(req.token)
        if password_reset_token is None:
            raise BadRequestException("El token no es válido.")
        if password_reset_token.utilizado:
            raise BadRequestException("El token ya fue utilizado.")
        if password_reset_token.fecha_expiracion < datetime.now():
            raise BadRequestException("El token ha expirado.")

        usuario = password_reset_token.usuario
        usuario.password = hash_password(req.nuevaPassword)
        password_reset_token.utilizado = True
        password_reset_token.estado = False
        self.user_repo.save(usuario)