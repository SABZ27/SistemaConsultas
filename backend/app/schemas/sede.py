from pydantic import BaseModel, ConfigDict, Field


class RegistroSedeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)


class UpdateSedeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)


class SedeResponse(BaseModel):
    id: int
    nombre: str
    estado: bool