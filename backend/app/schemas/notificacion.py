from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TipoNotificacion


class RegistroNotificacionRequest(BaseModel):
    remitenteId: int
    destinatarioId: int
    solicitudConsultaId: int
    tipo: TipoNotificacion
    titulo: str
    mensaje: str


class NotificacionResponse(BaseModel):
    id: int
    remitenteId: int
    nombreRemitente: str
    destinatarioId: int
    nombreDestinatario: str
    solicitudConsultaId: int
    numeroConsulta: str
    tipo: TipoNotificacion
    titulo: str
    mensaje: str
    leida: bool
    fechaCreacion: datetime


class MarcarNotificacionLeidaRequest(BaseModel):
    solicitudConsultaId: int
    leida: bool