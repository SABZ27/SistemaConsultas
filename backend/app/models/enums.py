from enum import Enum as PyEnum

from sqlalchemy import Enum as SaEnum


class Rol(str, PyEnum):
    ADMINISTRADOR = "ADMINISTRADOR"
    DOCENTE = "DOCENTE"
    ESTUDIANTE = "ESTUDIANTE"


class EstadoSolicitud(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    RECHAZADA = "RECHAZADA"
    EN_PROCESO = "EN_PROCESO"
    RESUELTA = "RESUELTA"
    CANCELADA = "CANCELADA"


class PrioridadSolicitud(str, PyEnum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class TipoRecursoFisico(str, PyEnum):
    SALON = "SALON"
    LABORATORIO = "LABORATORIO"
    AUDITORIO = "AUDITORIO"
    SALA = "SALA"
    OFICINA = "OFICINA"


class TipoNotificacion(str, PyEnum):
    NUEVA_SOLICITUD = "NUEVA_SOLICITUD"
    CAMBIO_ESTADO = "CAMBIO_ESTADO"
    REASIGNACION = "REASIGNACION"
    ASIGNACION_RECURSO = "ASIGNACION_RECURSO"
    CAMBIO_AGENDAMIENTO = "CAMBIO_AGENDAMIENTO"
    CANCELACION = "CANCELACION"
    COMENTARIO = "COMENTARIO"


class TipoEvento(str, PyEnum):
    CREACION = "CREACION"
    RECHAZO = "RECHAZO"
    CAMBIO_ESTADO = "CAMBIO_ESTADO"
    CANCELACION = "CANCELACION"
    ASIGNACION_RECURSO = "ASIGNACION_RECURSO"
    REASIGNACION_DOCENTE = "REASIGNACION_DOCENTE"
    COMENTARIO = "COMENTARIO"
    CAMBIO_AGENDAMIENTO = "CAMBIO_AGENDAMIENTO"


def _valores(miembros):
    return [m.value for m in miembros]


def columna_enum(enum_cls):
    return SaEnum(
        enum_cls,
        native_enum=False,
        length=50,
        values_callable=_valores,
        validate_strings=True,
    )