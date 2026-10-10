from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditoriaMixin, Base
from app.models.enums import EstadoSolicitud, PrioridadSolicitud, columna_enum


class SolicitudConsulta(AuditoriaMixin, Base):
    __tablename__ = "solicitudes_consultas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_consulta: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    estado_consulta: Mapped[EstadoSolicitud] = mapped_column(
        columna_enum(EstadoSolicitud), nullable=False, default=EstadoSolicitud.PENDIENTE
    )
    prioridad: Mapped[PrioridadSolicitud] = mapped_column(
        columna_enum(PrioridadSolicitud), nullable=False, default=PrioridadSolicitud.MEDIA
    )
    asunto: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_consulta: Mapped[date] = mapped_column(Date, nullable=False)
    hora_consulta: Mapped[time] = mapped_column(Time, nullable=False)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos.id"), nullable=False)
    recurso_fisico_id: Mapped[int | None] = mapped_column(ForeignKey("recursos_fisicos.id"), nullable=True)

    estudiante: Mapped["Usuario"] = relationship(foreign_keys=[estudiante_id], backref="solicitudes_estudiante")
    docente: Mapped["Usuario"] = relationship(foreign_keys=[docente_id], backref="solicitudes_docente")
    modulo: Mapped["Modulo"] = relationship(back_populates="solicitudes")
    recurso_fisico: Mapped["RecursoFisico | None"] = relationship(back_populates="solicitudes")
    comentarios: Mapped[list["Comentario"]] = relationship(back_populates="solicitudConsulta")
    eventos: Mapped[list["EventoSolicitud"]] = relationship(back_populates="solicitud")