from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base
from app.models.enums import Rol, columna_enum


class Usuario(AuditoriaMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        Index(
            "uq_usuarios_correo_estado",
            "correo",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
        Index(
            "uq_usuarios_identificacion_estado",
            "identificacion",
            unique=True,
            postgresql_where=text("estado"),
            sqlite_where=text("estado"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identificacion: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[Rol] = mapped_column(columna_enum(Rol), nullable=False, default=Rol.ESTUDIANTE)
    programa_id: Mapped[int | None] = mapped_column(ForeignKey("programas_academicos.id"), nullable=True)

    programa: Mapped["ProgramaAcademico | None"] = relationship(back_populates="usuarios")
    comentarios: Mapped[list["Comentario"]] = relationship(back_populates="autor")
    eventos: Mapped[list["EventoSolicitud"]] = relationship(back_populates="usuario")