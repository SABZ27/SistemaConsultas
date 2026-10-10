from pydantic import BaseModel, ConfigDict, Field


class RegistroProgAcademicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=4, max_length=100)


class UpdateProgAcademicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=4, max_length=100)


class ProgAcademicoResponse(BaseModel):
    id: int
    nombre: str
    estado: bool