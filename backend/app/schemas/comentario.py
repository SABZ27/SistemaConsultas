from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegistroComentarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contenido: str = Field(min_length=1)
    solicitudConsultaId: int


class UpdateComentarioRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    contenido: str = Field(min_length=1)


class ComentarioResponse(BaseModel):
    id: int
    autorId: int
    nombreAutor: str
    consultaId: int
    numeroConsulta: str
    contenido: str
    fechaCreacion: datetime
    editado: bool = False