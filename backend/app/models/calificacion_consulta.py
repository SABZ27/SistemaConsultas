from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class CalificacionConsulta(AuditoriaMixin, Base):
    __tablename__ = "calificaciones_consulta"
    __table_args__ = (
        CheckConstraint(
            "puntaje >= 1 AND puntaje <= 5",
            name="ck_calificaciones_consulta_puntaje",
        ),
        Index(
            "uq_calificaciones_consulta_solicitud",
            "solicitud_id",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_consultas.id"), nullable=False
    )
    puntaje: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    solicitud: Mapped["SolicitudConsulta"] = relationship(
        backref="calificacion"
    )
