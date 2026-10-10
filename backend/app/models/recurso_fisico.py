from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoRecursoFisico, columna_enum


class RecursoFisico(Base):
    __tablename__ = "recursos_fisicos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoRecursoFisico] = mapped_column(
        columna_enum(TipoRecursoFisico), nullable=False, default=TipoRecursoFisico.SALON
    )
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)
    bloque_id: Mapped[int] = mapped_column(ForeignKey("bloques.id"), nullable=False)

    bloque: Mapped["Bloque"] = relationship(back_populates="recursos_fisicos")
    solicitudes: Mapped[list["SolicitudConsulta"]] = relationship(back_populates="recurso_fisico")