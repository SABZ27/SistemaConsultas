from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, BeforeValidator

from app.models.enums import Rol
from app.schemas.validaciones import validar_correo

Correo = Annotated[str, BeforeValidator(validar_correo)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correo: str
    password: str


class LoginResponse(BaseModel):
    token: str
    id_usuario: int
    correo: str
    nombre: str
    rol: Rol
    tipo: str = "Bearer"


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    correo: Correo = Field(min_length=1, description="Correo del usuario")


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    token: str = Field(min_length=1)
    nuevaPassword: str = Field(min_length=8, max_length=100)