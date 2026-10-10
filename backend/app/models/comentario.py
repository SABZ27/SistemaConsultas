from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comentario(Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    editado: Mapped[bool] = mapped_column(nullable=True, default=False)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_consultas.id"), nullable=False)

    autor: Mapped["Usuario"] = relationship(back_populates="comentarios")
    solicitudConsulta: Mapped["SolicitudConsulta"] = relationship(back_populates="comentarios")