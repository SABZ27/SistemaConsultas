from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TipoEvento


class EventoSolicitudResponse(BaseModel):
    id: int
    solicitudId: int
    usuarioId: int
    nombreUsuario: str
    tipoEvento: TipoEvento
    descripcion: str
    fechaEvento: datetime