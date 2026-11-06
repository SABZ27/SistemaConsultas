from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.password_policy import PasswordPolicyError, validar_password
from app.models.enums import Rol
from app.schemas.auth import Correo


class RegistroUsuarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identificacion: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: Correo = Field(min_length=1)
    password: str
    rol: Rol
    programaId: int | None = None
    tipoDocumentoId: int | None = None

    @model_validator(mode="after")
    def _validar_password(self):
        error = validar_password(
            self.password,
            correo=self.correo,
            nombre=self.nombre,
            apellido=self.apellido,
            identificacion=self.identificacion,
        )
        if error:
            raise PasswordPolicyError(error, campo="password")
        return self


class UpdateUsuarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: Correo = Field(min_length=1)
    programaId: int | None = None
    tipoDocumentoId: int | None = None


class UsuarioResponse(BaseModel):
    id: int
    identificacion: str | None
    nombre: str
    apellido: str
    correo: str | None
    rol: Rol
    programaId: int | None
    programaNombre: str | None
    tipoDocumentoId: int | None
    tipoDocumentoSigla: str | None
    tipoDocumentoNombre: str | None
    estado: bool
    fechaCreacion: datetime
    # Aditivo del Bloque C: fecha de la última modificación.
    fechaActualizacion: datetime | None = None


class DocenteResumen(BaseModel):
    id: int
    nombre: str
    apellido: str