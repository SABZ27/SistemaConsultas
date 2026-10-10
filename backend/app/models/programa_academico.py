from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class ProgramaAcademico(AuditoriaMixin, Base):
    __tablename__ = "programas_academicos"
    __table_args__ = (
        Index(
            "uq_programas_academicos_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="programa")