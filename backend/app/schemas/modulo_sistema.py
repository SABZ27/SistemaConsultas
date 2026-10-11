from pydantic import BaseModel, ConfigDict, Field


class RegistroModuloSistemaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=200)
    ruta: str | None = Field(default=None, max_length=150)
    icono: str | None = Field(default=None, max_length=100)


class UpdateModuloSistemaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=200)
    ruta: str | None = Field(default=None, max_length=150)
    icono: str | None = Field(default=None, max_length=100)


class ModuloSistemaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    ruta: str | None
    icono: str | None
    estado: bool