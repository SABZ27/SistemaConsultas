from app.db.base import Base

from app.models.programa_academico import ProgramaAcademico
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.modulo import Modulo
from app.models.modulo_sistema import ModuloSistema
from app.models.modulo_x_rol import ModuloXRol
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.comentario import Comentario
from app.models.evento_solicitud import EventoSolicitud
from app.models.notificacion import Notificacion
from app.models.password_reset_token import PasswordResetToken

__all__ = [
    "Base",
    "ProgramaAcademico",
    "Rol",
    "Usuario",
    "Modulo",
    "ModuloSistema",
    "ModuloXRol",
    "SolicitudConsulta",
    "Comentario",
    "EventoSolicitud",
    "Notificacion",
    "PasswordResetToken",
]