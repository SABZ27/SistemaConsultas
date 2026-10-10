from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Bloque(Base):
    __tablename__ = "bloques"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id"), nullable=False)

    sede: Mapped["Sede"] = relationship(back_populates="bloques")
    recursos_fisicos: Mapped[list["RecursoFisico"]] = relationship(back_populates="bloque")