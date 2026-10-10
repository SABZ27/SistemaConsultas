from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import EstadoSolicitud, PrioridadSolicitud


class RegistroSolicitudConsultaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prioridad: PrioridadSolicitud
    asunto: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1)
    fechaConsulta: date
    horaConsulta: time
    docenteId: int
    moduloId: int


class UpdateSolicitudConsultaRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prioridad: PrioridadSolicitud
    asunto: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1)
    fechaConsulta: date
    horaConsulta: time
    moduloId: int
    motivo: str | None = None


class AsignarRecursoFisicoRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recursoFisicoId: int


class ReasignarDocenteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    docenteId: int


class CambiarEstadoSolicitudRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    estado: EstadoSolicitud
    motivo: str | None = None


class SolicitudConsultaResponse(BaseModel):
    id: int
    numeroConsulta: str
    estado: EstadoSolicitud
    prioridad: PrioridadSolicitud
    asunto: str
    descripcion: str
    fechaCreacion: datetime
    fechaConsulta: date
    horaConsulta: time
    estudianteId: int
    identificacionEstudiante: str
    nombreCompletoEstudiante: str
    docenteId: int
    identificacionDocente: str
    nombreCompletoDocente: str
    moduloId: int
    nombreModulo: str
    nombrePrograma: str | None = "Sin programa"
    recursoFisicoId: int | None = None
    nombreRecursoFisico: str | None = "Sin asignar"

    @field_serializer("horaConsulta")
    def serializar_hora(self, valor: time, _info) -> str:
        return valor.strftime("%H:%M")

    @field_serializer("fechaConsulta")
    def serializar_fecha(self, valor: date, _info) -> str:
        return valor.strftime("%Y-%m-%d")