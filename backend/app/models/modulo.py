from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class Modulo(AuditoriaMixin, Base):
    __tablename__ = "modulos"
    __table_args__ = (
        Index(
            "uq_modulos_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    solicitudes: Mapped[list["SolicitudConsulta"]] = relationship(back_populates="modulo")