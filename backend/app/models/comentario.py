import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class Comentario(AuditoriaMixin, Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(
        String(36), nullable=False, default=lambda: str(uuid.uuid4()), unique=True
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    editado: Mapped[bool] = mapped_column(nullable=True, default=False)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_consultas.id"), nullable=False)

    autor: Mapped["Usuario"] = relationship(back_populates="comentarios")
    solicitudConsulta: Mapped["SolicitudConsulta"] = relationship(back_populates="comentarios")