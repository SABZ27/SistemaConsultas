from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, BeforeValidator, model_validator

from app.core.password_policy import PasswordPolicyError, validar_password
from app.models.enums import Rol
from app.schemas.validaciones import validar_correo

Correo = Annotated[str, BeforeValidator(validar_correo)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correo: str
    password: str


class ModuloInfo(BaseModel):
    nombre: str
    ruta: str | None
    icono: str | None


class LoginResponse(BaseModel):
    token: str
    id_usuario: int
    correo: str
    nombre: str
    rol: Rol
    tipo: str = "Bearer"
    modulos: list[ModuloInfo]


class MeResponse(BaseModel):
    id: int
    identificacion: str
    correo: str
    nombre: str
    rol: Rol
    modulos: list[ModuloInfo]


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correo: Correo = Field(min_length=1, description="Correo del usuario")


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    token: str = Field(min_length=1)
    nuevaPassword: str

    @model_validator(mode="after")
    def _validar_nueva_password(self):
        error = validar_password(self.nuevaPassword)
        if error:
            raise PasswordPolicyError(error, campo="nuevaPassword")
        return self


class CambiarPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    passwordActual: str = Field(min_length=1)
    nuevaPassword: str

    @model_validator(mode="after")
    def _validar_nueva_password(self):
        error = validar_password(self.nuevaPassword)
        if error:
            raise PasswordPolicyError(error, campo="nuevaPassword")
        return self