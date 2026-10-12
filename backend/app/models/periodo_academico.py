from datetime import date

from sqlalchemy import CheckConstraint, Date, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditoriaMixin, Base


class PeriodoAcademico(AuditoriaMixin, Base):
    __tablename__ = "periodos_academicos"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin > fecha_inicio",
            name="ck_periodos_academicos_rango",
        ),
        Index(
            "uq_periodos_academicos_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
