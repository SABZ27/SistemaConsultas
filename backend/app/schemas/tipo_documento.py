from pydantic import BaseModel, ConfigDict, Field


class RegistroTipoDocumentoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    sigla: str = Field(min_length=1, max_length=10)


class UpdateTipoDocumentoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    sigla: str = Field(min_length=1, max_length=10)


class TipoDocumentoResponse(BaseModel):
    id: int
    nombre: str
    sigla: str
    estado: bool
