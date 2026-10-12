from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class DisponibilidadDocente(AuditoriaMixin, Base):
    __tablename__ = "disponibilidad_docente"
    __table_args__ = (
        CheckConstraint(
            "dia_semana >= 1 AND dia_semana <= 7",
            name="ck_disponibilidad_docente_dia_semana",
        ),
        CheckConstraint(
            "hora_fin > hora_inicio",
            name="ck_disponibilidad_docente_horas",
        ),
        Index(
            "uq_disponibilidad_docente_docente_dia_hora",
            "docente_id",
            "dia_semana",
            "hora_inicio",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)

    docente: Mapped["Usuario"] = relationship(foreign_keys=[docente_id])
