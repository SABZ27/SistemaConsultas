from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class ModuloSistema(AuditoriaMixin, Base):
    __tablename__ = "modulos_sistema"
    __table_args__ = (
        Index(
            "uq_modulos_sistema_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ruta: Mapped[str | None] = mapped_column(String(150), nullable=True)
    icono: Mapped[str | None] = mapped_column(String(100), nullable=True)

    roles: Mapped[list["ModuloXRol"]] = relationship(back_populates="modulo_sistema")