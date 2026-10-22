from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class Zona(AuditoriaMixin, Base):
    __tablename__ = "zonas"
    __table_args__ = (
        Index(
            "uq_zonas_sede_nombre_estado",
            "sede_id",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    sede: Mapped["Sede"] = relationship(back_populates="zonas")
    recursos: Mapped[list["RecursoFisico"]] = relationship(back_populates="zona")
