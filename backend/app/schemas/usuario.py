from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Rol
from app.schemas.auth import Correo


class RegistroUsuarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identificacion: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: Correo = Field(min_length=1)
    password: str = Field(min_length=8, max_length=100)
    rol: Rol
    programaId: int | None = None


class UpdateUsuarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: Correo = Field(min_length=1)
    programaId: int | None = None


class UsuarioResponse(BaseModel):
    id: int
    identificacion: str
    nombre: str
    apellido: str
    correo: str
    rol: Rol
    programaId: int | None
    programaNombre: str | None
    estado: bool
    fechaCreacion: datetime