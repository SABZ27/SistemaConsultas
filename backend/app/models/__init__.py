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
from app.models.docente_modulo import DocenteModulo
from app.models.tipo_documento import TipoDocumento
from app.models.calificacion_consulta import CalificacionConsulta
from app.models.periodo_academico import PeriodoAcademico
from app.models.disponibilidad_docente import DisponibilidadDocente
from app.models.sede import Sede
from app.models.zona import Zona
from app.models.recurso_fisico import RecursoFisico

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
    "DocenteModulo",
    "TipoDocumento",
    "CalificacionConsulta",
    "PeriodoAcademico",
    "DisponibilidadDocente",
    "Sede",
    "Zona",
    "RecursoFisico",
]
