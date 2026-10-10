from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoNotificacion, columna_enum


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    remitente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    destinatario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    solicitud_consulta_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_consultas.id"), nullable=False)
    tipo: Mapped[TipoNotificacion] = mapped_column(columna_enum(TipoNotificacion), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(500), nullable=False)
    leida: Mapped[bool] = mapped_column(nullable=False, default=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    remitente: Mapped["Usuario"] = relationship(foreign_keys=[remitente_id])
    destinatario: Mapped["Usuario"] = relationship(foreign_keys=[destinatario_id])
    solicitudConsulta: Mapped["SolicitudConsulta"] = relationship()