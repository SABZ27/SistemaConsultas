from pydantic import BaseModel, ConfigDict, Field


class RegistroModuloRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    descripcion: str = Field(min_length=10, max_length=500)


class UpdateModuloRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    descripcion: str = Field(min_length=10, max_length=500)


class ModuloResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool