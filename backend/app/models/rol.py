from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class Rol(AuditoriaMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        Index(
            "uq_roles_nombre_estado",
            "nombre",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol_rel")
    modulos: Mapped[list["ModuloXRol"]] = relationship(back_populates="rol")