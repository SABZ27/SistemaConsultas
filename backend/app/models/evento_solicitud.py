import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base
from app.models.enums import TipoEvento, columna_enum


class EventoSolicitud(AuditoriaMixin, Base):
    __tablename__ = "eventos_solicitud"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(
        String(36), nullable=False, default=lambda: str(uuid.uuid4()), unique=True
    )
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_consultas.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo_evento: Mapped[TipoEvento] = mapped_column(columna_enum(TipoEvento), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    fecha_evento: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    solicitud: Mapped["SolicitudConsulta"] = relationship(back_populates="eventos")
    usuario: Mapped["Usuario"] = relationship(back_populates="eventos")