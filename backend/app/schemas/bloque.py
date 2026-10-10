from pydantic import BaseModel, ConfigDict, Field


class RegistroBloqueRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)
    sedeId: int


class UpdateBloqueRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)


class BloqueResponse(BaseModel):
    id: int
    nombre: str
    sedeId: int
    sedeNombre: str
    activo: bool