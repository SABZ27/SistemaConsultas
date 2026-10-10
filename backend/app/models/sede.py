from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)

    bloques: Mapped[list["Bloque"]] = relationship(back_populates="sede")