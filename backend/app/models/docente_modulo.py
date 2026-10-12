from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class DocenteModulo(AuditoriaMixin, Base):
    __tablename__ = "docentes_modulos"
    __table_args__ = (
        Index(
            "uq_docentes_modulos_docente_modulo",
            "docente_id",
            "modulo_id",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos.id"), nullable=False)

    docente: Mapped["Usuario"] = relationship(foreign_keys=[docente_id])
    modulo: Mapped["Modulo"] = relationship(foreign_keys=[modulo_id])
