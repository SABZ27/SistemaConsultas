from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoEstructura


class RegistroSedeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    tipoEstructura: TipoEstructura


class UpdateSedeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    tipoEstructura: TipoEstructura


class SedeResponse(BaseModel):
    id: int
    nombre: str
    tipoEstructura: TipoEstructura
    estado: bool
