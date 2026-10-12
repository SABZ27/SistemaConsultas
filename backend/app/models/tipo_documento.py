from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class TipoDocumento(AuditoriaMixin, Base):
    __tablename__ = "tipos_documento"
    __table_args__ = (
        Index(
            "uq_tipos_documento_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
        Index(
            "uq_tipos_documento_sigla_estado",
            "sigla",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    sigla: Mapped[str] = mapped_column(String(10), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="tipo_documento")
