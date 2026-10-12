from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class RegistroDisponibilidadRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    docenteId: int | None = None
    diaSemana: int = Field(ge=1, le=7)
    horaInicio: time
    horaFin: time


class UpdateDisponibilidadRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    diaSemana: int = Field(ge=1, le=7)
    horaInicio: time
    horaFin: time


class DisponibilidadResponse(BaseModel):
    id: int
    docenteId: int
    nombreDocente: str
    diaSemana: int
    horaInicio: time
    horaFin: time
    estado: bool

    @field_serializer("horaInicio", "horaFin")
    def serializar_hora(self, valor: time, _info) -> str:
        return valor.strftime("%H:%M")
