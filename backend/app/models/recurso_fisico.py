from typing import Optional

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base
from app.models.enums import TipoRecursoFisico, columna_enum


class RecursoFisico(AuditoriaMixin, Base):
    __tablename__ = "recursos_fisicos"
    __table_args__ = (
        Index(
            "uq_recursos_sede_zona_nombre_estado",
            "sede_id",
            "zona_id",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)
    zona_id: Mapped[int | None] = mapped_column(ForeignKey("zonas.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoRecursoFisico] = mapped_column(
        columna_enum(TipoRecursoFisico), nullable=False, default=TipoRecursoFisico.SALON
    )

    sede: Mapped["Sede"] = relationship(back_populates="recursos")
    zona: Mapped[Optional["Zona"]] = relationship(back_populates="recursos")
