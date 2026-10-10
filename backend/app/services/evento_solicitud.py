from datetime import datetime

from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException
from app.models.enums import EstadoSolicitud, TipoEvento
from app.models.evento_solicitud import EventoSolicitud
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.usuario import Usuario
from app.repositories.evento_solicitud import EventoSolicitudRepository


class EventoSolicitudService:
    def __init__(self, db: Session):
        self.repo = EventoSolicitudRepository(db)

    def _registrar_evento(
        self,
        solicitud: SolicitudConsulta,
        usuario: Usuario,
        tipo_evento: TipoEvento,
        descripcion: str,
    ) -> None:
        evento = EventoSolicitud(
            solicitud=solicitud,
            usuario=usuario,
            tipo_evento=tipo_evento,
            descripcion=descripcion,
            fecha_evento=datetime.now(),
        )
        self.repo.save(evento)

    def nueva_solicitud(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        self._registrar_evento(
            solicitud,
            usuario,
            TipoEvento.CREACION,
            f"{usuario.nombre} {usuario.apellido} ha creado la solicitud de consulta {solicitud.numero_consulta}.",
        )

    def cambio_estado(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        self._registrar_evento(
            solicitud,
            usuario,
            self._obtener_tipo_evento(solicitud.estado),
            self._obtener_contenido_descripcion(solicitud, usuario),
        )

    def cambio_agenda(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        self._registrar_evento(
            solicitud,
            usuario,
            TipoEvento.CAMBIO_AGENDAMIENTO,
            f"{usuario.nombre} {usuario.apellido} reprogramó la consulta para el {solicitud.fecha_consulta} a las {solicitud.hora_consulta}.",
        )

    def asignacion_recurso(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        recurso = solicitud.recurso_fisico
        if recurso is None:
            raise BadRequestException("La solicitud no tiene un recurso físico asignado.")
        self._registrar_evento(
            solicitud,
            usuario,
            TipoEvento.ASIGNACION_RECURSO,
            f"{usuario.nombre} {usuario.apellido} asignó el recurso {recurso.nombre} a la consulta.",
        )

    def reasignacion(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        self._registrar_evento(
            solicitud,
            usuario,
            TipoEvento.REASIGNACION_DOCENTE,
            f"{usuario.nombre} {usuario.apellido} le reasignó la consulta al docente: {solicitud.docente.nombre} {solicitud.docente.apellido}.",
        )

    def nuevo_comentario(self, solicitud: SolicitudConsulta, usuario: Usuario) -> None:
        self._registrar_evento(
            solicitud,
            usuario,
            TipoEvento.COMENTARIO,
            f"{usuario.nombre} {usuario.apellido} agregó un comentario a la consulta.",
        )

    def _obtener_tipo_evento(self, estado: EstadoSolicitud) -> TipoEvento:
        if estado == EstadoSolicitud.RECHAZADA:
            return TipoEvento.RECHAZO
        if estado == EstadoSolicitud.CANCELADA:
            return TipoEvento.CANCELACION
        if estado in (EstadoSolicitud.RESUELTA, EstadoSolicitud.EN_PROCESO):
            return TipoEvento.CAMBIO_ESTADO
        raise BadRequestException(f"No existe evento definido para el estado {estado}")

    def _obtener_contenido_descripcion(
        self, solicitud: SolicitudConsulta, usuario: Usuario
    ) -> str:
        if solicitud.estado == EstadoSolicitud.EN_PROCESO:
            return (
                f"EL docente {usuario.nombre} {usuario.apellido} "
                "cambió el estado de la solicitud a EN_PROCESO.."
            )
        if solicitud.estado == EstadoSolicitud.RESUELTA:
            return (
                f"El docente {usuario.nombre} {usuario.apellido} "
                "cambió el estado de la consulta a RESUELTA."
            )
        if solicitud.estado == EstadoSolicitud.CANCELADA:
            return f"{usuario.nombre} {usuario.apellido} ha cancelado la solicitud de consulta."
        if solicitud.estado == EstadoSolicitud.RECHAZADA:
            return f"{usuario.nombre} {usuario.apellido} ha rechazado la solicitud de consulta."
        raise BadRequestException(
            f"No existe evento definido para el estado {solicitud.estado}"
        )