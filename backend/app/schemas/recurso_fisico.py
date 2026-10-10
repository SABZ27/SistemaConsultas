from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoRecursoFisico


class RegistroRecursoFisicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)
    tipo: TipoRecursoFisico
    bloqueId: int


class UpdateRecursoFisicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=1, max_length=100)


class RecursoFisicoResponse(BaseModel):
    id: int
    nombre: str
    bloqueId: int
    bloqueNombre: str
    tipo: TipoRecursoFisico
    activo: bool