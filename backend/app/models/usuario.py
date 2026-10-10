from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Rol, columna_enum


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identificacion: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[Rol] = mapped_column(columna_enum(Rol), nullable=False, default=Rol.ESTUDIANTE)
    programa_id: Mapped[int | None] = mapped_column(ForeignKey("programas_academicos.id"), nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    programa: Mapped["ProgramaAcademico | None"] = relationship(back_populates="usuarios")
    comentarios: Mapped[list["Comentario"]] = relationship(back_populates="autor")
    eventos: Mapped[list["EventoSolicitud"]] = relationship(back_populates="usuario")