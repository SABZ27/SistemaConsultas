from app.db.base import Base

from app.models.programa_academico import ProgramaAcademico
from app.models.usuario import Usuario
from app.models.modulo import Modulo
from app.models.sede import Sede
from app.models.bloque import Bloque
from app.models.recurso_fisico import RecursoFisico
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.comentario import Comentario
from app.models.evento_solicitud import EventoSolicitud
from app.models.notificacion import Notificacion
from app.models.password_reset_token import PasswordResetToken

__all__ = [
    "Base",
    "ProgramaAcademico",
    "Usuario",
    "Modulo",
    "Sede",
    "Bloque",
    "RecursoFisico",
    "SolicitudConsulta",
    "Comentario",
    "EventoSolicitud",
    "Notificacion",
    "PasswordResetToken",
]