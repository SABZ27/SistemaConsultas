from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base


class ModuloXRol(AuditoriaMixin, Base):
    __tablename__ = "modulos_x_rol"
    __table_args__ = (
        Index(
            "uq_modulos_x_rol_rol_modulo",
            "rol_id",
            "modulo_id",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos_sistema.id"), nullable=False)

    rol: Mapped["Rol"] = relationship(back_populates="modulos")
    modulo_sistema: Mapped["ModuloSistema"] = relationship(back_populates="roles")