from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Modulo(Base):
    __tablename__ = "modulos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)

    solicitudes: Mapped[list["SolicitudConsulta"]] = relationship(back_populates="modulo")