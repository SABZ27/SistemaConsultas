from pydantic import BaseModel, ConfigDict, Field


class RegistroRolRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=200)


class UpdateRolRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=200)


class RolResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    estado: bool


class ModuloAsignacionResponse(BaseModel):
    id: int
    nombre: str
    ruta: str | None
    icono: str | None


class AsignarModulosRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    moduloIds: list[int]