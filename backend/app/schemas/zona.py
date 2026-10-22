from pydantic import BaseModel, ConfigDict, Field


class RegistroZonaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sedeId: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=100)


class UpdateZonaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sedeId: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=100)


class ZonaResponse(BaseModel):
    id: int
    sedeId: int
    nombre: str
    estado: bool
