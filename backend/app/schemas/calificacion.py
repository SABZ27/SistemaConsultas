from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CalificacionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    puntaje: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=500)


class CalificacionResponse(BaseModel):
    id: int
    solicitudId: int
    puntaje: int
    comentario: str | None
    docenteId: int
    estudianteId: int
    fechaCreacion: datetime


class PromedioCalificacionesResponse(BaseModel):
    docenteId: int
    promedio: float
    total: int
