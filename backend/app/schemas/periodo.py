from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class RegistroPeriodoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    fechaInicio: date
    fechaFin: date


class UpdatePeriodoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str = Field(min_length=3, max_length=100)
    fechaInicio: date
    fechaFin: date


class PeriodoResponse(BaseModel):
    id: int
    nombre: str
    fechaInicio: date
    fechaFin: date
    estado: bool
