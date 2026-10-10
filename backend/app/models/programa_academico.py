from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProgramaAcademico(Base):
    __tablename__ = "programas_academicos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="programa")