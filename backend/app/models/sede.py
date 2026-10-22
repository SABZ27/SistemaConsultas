from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base
from app.models.enums import TipoEstructura, columna_enum


class Sede(AuditoriaMixin, Base):
    __tablename__ = "sedes"
    __table_args__ = (
        Index(
            "uq_sedes_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_estructura: Mapped[TipoEstructura] = mapped_column(
        columna_enum(TipoEstructura), nullable=False, default=TipoEstructura.BLOQUES
    )

    zonas: Mapped[list["Zona"]] = relationship(back_populates="sede")
    recursos: Mapped[list["RecursoFisico"]] = relationship(back_populates="sede")
