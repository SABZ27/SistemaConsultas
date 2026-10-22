from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoRecursoFisico


class RegistroRecursoFisicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sedeId: int = Field(gt=0)
    zonaId: int | None = Field(default=None, gt=0)
    nombre: str = Field(min_length=1, max_length=100)
    tipo: TipoRecursoFisico = TipoRecursoFisico.SALON


class UpdateRecursoFisicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sedeId: int = Field(gt=0)
    zonaId: int | None = Field(default=None, gt=0)
    nombre: str = Field(min_length=1, max_length=100)
    tipo: TipoRecursoFisico = TipoRecursoFisico.SALON


class RecursoFisicoResponse(BaseModel):
    id: int
    sedeId: int
    zonaId: int | None
    nombre: str
    tipo: TipoRecursoFisico
    ubicacion: str
    estado: bool
