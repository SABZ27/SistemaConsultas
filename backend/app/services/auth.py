from datetime import datetime, timedelta

from fastapi import HTTPException

from app.core.password_policy import validar_password
from app.core.rate_limit import (
    LIMITE_FORGOT_CORREO,
    LIMITE_FORGOT_IP,
    LIMITE_LOGIN_CORREO,
    LIMITE_LOGIN_IP,
    LIMITE_LOGIN_PAR,
    LIMITE_REGISTRO_CORREO,
    LIMITE_REGISTRO_IP,
    LIMITE_RESET_IP,
    LIMITE_RESET_TOKEN,
    MENSAJE_DEMASIADAS_SOLICITUDES,
    MENSAJE_DEMASIADOS_INTENTOS,
    ResultadoLimite,
)
from app.core.security import (
    create_access_token,
    generar_token_reset,
    hash_password,
    hash_token,
    verify_password,
)
from app.exceptions.errors import BadRequestException, TooManyRequestsException
from app.mappers.usuario import nombre_completo
from app.models.enums import Rol
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.password_reset_token import PasswordResetTokenRepository
from app.repositories.usuario import UsuarioRepository
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
from app.services.email import CorreoPendiente
from app.services.usuario import UsuarioService


class AuthService:
    def __init__(self, db):
        self.db = db
        self.user_repo = UsuarioRepository(db)
        self.mxl_repo = ModuloXRolRepository(db)
        self.token_repo = PasswordResetTokenRepository(db)
        self.usuario_service = UsuarioService(db)

    def login(self, req: LoginRequest, ip: str = "desconocida") -> LoginResponse:
        correo = (req.correo or "").strip().lower()
        par = f"{correo}|{ip}"

        resultado = self._comprobar_limites_login(par, correo, ip)
        if not resultado.permitido:
            raise TooManyRequestsException(
                MENSAJE_DEMASIADOS_INTENTOS,
                retry_after=resultado.reintentar_en,
            )

        usuario = self.user_repo.find_by_correo_and_estado_true(req.correo)
        if usuario is None or not verify_password(req.password, usuario.password):
            LIMITE_LOGIN_PAR.registrar_fallo(par)
            LIMITE_LOGIN_CORREO.registrar_fallo(correo)
            LIMITE_LOGIN_IP.registrar_fallo(ip)
            raise HTTPException(
                status_code=401, detail="Correo o contraseña incorrectos."
            )

        # Un login correcto limpia solo la pareja correo+IP. Los contadores
        # solo-correo y solo-IP se conservan para frenar ataques distribuidos.
        LIMITE_LOGIN_PAR.limpiar(par)

        modulos = self.mxl_repo.activos_por_rol(usuario.rol_id)
        nombres_modulos = [m.nombre for m in modulos]
        token = create_access_token(
            usuario.correo, usuario.id, usuario.rol.value, nombres_modulos
        )
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

    def registro(self, req: RegistroUsuarioRequest, ip: str = "desconocida") -> None:
        correo = (req.correo or "").strip().lower()
        self._exigir_limite(LIMITE_REGISTRO_IP, ip)
        self._exigir_limite(LIMITE_REGISTRO_CORREO, correo)

        if req.rol == Rol.ADMINISTRADOR:
            raise HTTPException(
                status_code=403,
                detail="El registro no permite crear usuarios con rol ADMINISTRADOR.",
            )
        self.usuario_service.crear_usuario(req)

    def forgot_password(
        self, req: ForgotPasswordRequest, ip: str = "desconocida"
    ) -> CorreoPendiente | None:
        correo = (req.correo or "").strip().lower()
        self._exigir_limite(LIMITE_FORGOT_IP, ip)
        self._exigir_limite(LIMITE_FORGOT_CORREO, correo)

        usuario = self.user_repo.find_by_correo_and_estado_true(req.correo)
        if usuario is None:
            # Misma respuesta que cuando existe, sin enviar correo.
            return None

        self.token_repo.delete_by_usuario_id(usuario.id)
        token_plano = generar_token_reset()
        self.token_repo.save(
            PasswordResetToken(
                token=hash_token(token_plano),
                usuario=usuario,
                fecha_expiracion=datetime.now() + timedelta(minutes=30),
                utilizado=False,
            )
        )
        return CorreoPendiente(
            para=usuario.correo,
            para_nombre=f"{usuario.nombre} {usuario.apellido}",
            asunto="Recuperación de contraseña",
            contenido=(
                f"Hola {usuario.nombre},\n\n"
                "Has solicitado recuperar tu contraseña.\n\n"
                "Utiliza el siguiente token para restablecerla:\n\n"
                f"{token_plano}\n\n"
                "Este token expira en 30 minutos."
            ),
        )

    def reset_password(
        self, req: ResetPasswordRequest, ip: str = "desconocida"
    ) -> None:
        token_hash = hash_token(req.token)
        self._exigir_limite(LIMITE_RESET_IP, ip)
        self._exigir_limite(LIMITE_RESET_TOKEN, token_hash)

        password_reset_token = self.token_repo.find_by_token(token_hash)
        if password_reset_token is None:
            raise BadRequestException("El token no es válido.")
        if password_reset_token.utilizado:
            raise BadRequestException("El token ya fue utilizado.")
        if password_reset_token.fecha_expiracion < datetime.now():
            raise BadRequestException("El token ha expirado.")

        usuario = password_reset_token.usuario
        error = validar_password(
            req.nuevaPassword,
            correo=usuario.correo,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            identificacion=usuario.identificacion,
        )
        if error:
            raise BadRequestException(error, errors={"nuevaPassword": error})

        usuario.password = hash_password(req.nuevaPassword)
        password_reset_token.utilizado = True
        password_reset_token.estado = False
        self.user_repo.save(usuario)

    def cambiar_password(self, usuario: Usuario, req: CambiarPasswordRequest) -> None:
        if not verify_password(req.passwordActual, usuario.password):
            raise BadRequestException("La contraseña actual es incorrecta.")
        if verify_password(req.nuevaPassword, usuario.password):
            mensaje = "La nueva contraseña debe ser diferente a la actual."
            raise BadRequestException(mensaje, errors={"nuevaPassword": mensaje})

        error = validar_password(
            req.nuevaPassword,
            correo=usuario.correo,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            identificacion=usuario.identificacion,
        )
        if error:
            raise BadRequestException(error, errors={"nuevaPassword": error})

        usuario.password = hash_password(req.nuevaPassword)
        self.user_repo.save(usuario)

    def _comprobar_limites_login(
        self, par: str, correo: str, ip: str
    ) -> ResultadoLimite:
        for limitador, clave in (
            (LIMITE_LOGIN_PAR, par),
            (LIMITE_LOGIN_CORREO, correo),
            (LIMITE_LOGIN_IP, ip),
        ):
            resultado = limitador.esta_bloqueado(clave)
            if not resultado.permitido:
                return resultado
        return ResultadoLimite(True, 0)

    def _exigir_limite(self, limitador, clave: str) -> None:
        resultado = limitador.permitir(clave)
        if not resultado.permitido:
            raise TooManyRequestsException(
                MENSAJE_DEMASIADAS_SOLICITUDES,
                retry_after=resultado.reintentar_en,
            )
