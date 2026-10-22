from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.notificacion import notificacion_response
from app.models.comentario import Comentario
from app.models.enums import EstadoSolicitud, TipoNotificacion
from app.models.notificacion import Notificacion
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.usuario import Usuario
from app.repositories.notificacion import NotificacionRepository
from app.repositories.solicitud_consulta import SolicitudConsultaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.notificacion import RegistroNotificacionRequest
from app.services.email import CorreoPendiente


class NotificacionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificacionRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.solicitud_repo = SolicitudConsultaRepository(db)
        # Correos que el servicio deja pendiente de envío. Los despacha la
        # capa de API en segundo plano (después del commit de la transacción).
        self.correos_pendientes: list[CorreoPendiente] = []

    def _obtener_usuario(self, id_usuario: int) -> Usuario:
        usuario = self.user_repo.find_by_id_and_estado_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        return usuario

    def _obtener_solicitud(self, id_solicitud: int):
        solicitud = self.solicitud_repo.find_by_id(id_solicitud)
        if solicitud is None:
            raise ResourceNotFoundException("Solicitud no encontrada.")
        return solicitud

    def _registrar_notificacion(
        self,
        request: RegistroNotificacionRequest,
    ):
        remitente = self._obtener_usuario(request.remitenteId)
        destinatario = self._obtener_usuario(request.destinatarioId)
        consulta = self._obtener_solicitud(request.solicitudConsultaId)
        notificacion = Notificacion(
            remitente=remitente,
            destinatario=destinatario,
            solicitudConsulta=consulta,
            tipo=request.tipo,
            titulo=request.titulo,
            leida=False,
            mensaje=request.mensaje,
        )

        notificacion_guardada = self.repo.save(notificacion)
        if request.tipo != TipoNotificacion.COMENTARIO:
            self.correos_pendientes.append(
                CorreoPendiente(
                    para=destinatario.correo,
                    para_nombre=f"{destinatario.nombre} {destinatario.apellido}",
                    asunto=notificacion.titulo,
                    contenido=notificacion.mensaje,
                )
            )
        return notificacion_guardada

    def _armar_notificacion(
        self,
        remitente: Usuario,
        destinatario_id: int,
        tipo: TipoNotificacion,
        solicitud_id: int,
        titulo: str,
        mensaje: str,
    ):
        return self._registrar_notificacion(
            RegistroNotificacionRequest(
                remitenteId=remitente.id,
                destinatarioId=destinatario_id,
                solicitudConsultaId=solicitud_id,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
            )
        )

    def notificar_nueva_solicitud(
        self, solicitud: SolicitudConsulta, remitente: Usuario
    ) -> None:
        self._armar_notificacion(
            remitente,
            solicitud.docente_id,
            TipoNotificacion.NUEVA_SOLICITUD,
            solicitud.id,
            "Nueva solicitud de consulta",
            (
                f"El estudiante {solicitud.estudiante.nombre} {solicitud.estudiante.apellido} "
                f"ha creado una nueva solicitud de consulta con el número {solicitud.numero_consulta}.\n"
                "Revisa los detalles de la solicitud para gestionar su atención."
            ),
        )

    def notificar_cambio_agenda(
        self,
        solicitud: SolicitudConsulta,
        destinatario: Usuario,
        motivo: str,
        remitente: Usuario,
    ) -> None:
        self._armar_notificacion(
            remitente,
            destinatario.id,
            TipoNotificacion.CAMBIO_AGENDAMIENTO,
            solicitud.id,
            "Cambio en la agenda de tu consulta",
            (
                f"La consulta {solicitud.numero_consulta} ha sido reprogramada para el "
                f"{solicitud.fecha_consulta} a las {solicitud.hora_consulta}.\n"
                f"Motivo: {motivo}"
            ),
        )

    def notificar_cambio_estado(
        self,
        solicitud: SolicitudConsulta,
        destinatario: Usuario,
        motivo: str | None,
        remitente: Usuario,
    ) -> None:
        titulo, mensaje = self._obtener_contenido_notificacion(solicitud, motivo)
        tipo_notificacion = self._obtener_tipo_notificacion(solicitud.estado_consulta)
        self._armar_notificacion(
            remitente,
            destinatario.id,
            tipo_notificacion,
            solicitud.id,
            titulo,
            mensaje,
        )

    def notificar_asignacion_recurso(
        self,
        solicitud: SolicitudConsulta,
        destinatario: Usuario,
        remitente: Usuario,
    ) -> None:
        self._armar_notificacion(
            remitente,
            destinatario.id,
            TipoNotificacion.ASIGNACION_RECURSO,
            solicitud.id,
            "Recurso físico asignado",
            (
                f"Se ha asignado el recurso {solicitud.recurso_fisico_nombre} para la consulta "
                f"{solicitud.numero_consulta}.\n"
                "Consulta los detalles de tu solicitud para conocer la información actualizada."
            ),
        )

    def notificar_reasignacion(
        self,
        solicitud: SolicitudConsulta,
        nuevo_docente: Usuario,
        remitente: Usuario,
    ) -> None:
        self._armar_notificacion(
            remitente,
            nuevo_docente.id,
            TipoNotificacion.REASIGNACION,
            solicitud.id,
            "Reasignación de consulta",
            (
                f"Una nueva solicitud de consulta con el número {solicitud.numero_consulta} "
                "le ha sido asignada.\n"
                "Revisa los detalles de la solicitud para gestionar su atención."
            ),
        )

    def notificar_comentario(
        self, comentario: Comentario, destinatario: Usuario, remitente: Usuario
    ) -> None:
        self._armar_notificacion(
            remitente,
            destinatario.id,
            TipoNotificacion.COMENTARIO,
            comentario.solicitud_id,
            f"Nuevo comentario en la consulta {comentario.solicitudConsulta.numero_consulta}",
            (
                f"{comentario.autor.nombre} {comentario.autor.apellido} "
                f"ha agregado un nuevo comentario: {comentario.contenido}"
            ),
        )

    def listar_notificaciones(self, usuario_actual: Usuario):
        return [
            notificacion_response(n)
            for n in self.repo.find_all_by_destinatario_id(usuario_actual.id)
        ]

    def contar_notificaciones_no_leidas(self, usuario_actual: Usuario) -> int:
        return self.repo.count_by_destinatario_and_leida_false(usuario_actual.id)

    def marcar_como_leida(self, id_notificacion: int, usuario_actual: Usuario):
        notificacion = self.repo.find_by_id(id_notificacion)
        if notificacion is None:
            raise ResourceNotFoundException("Notificación no encontrada.")

        if usuario_actual.id != notificacion.destinatario_id:
            raise BadRequestException("Esta notificación no le pertenece.")

        notificacion.leida = True
        return notificacion_response(self.repo.save(notificacion))

    def eliminar(self, id_notificacion: int, usuario_actual: Usuario) -> None:
        notificacion = self.repo.find_by_id(id_notificacion)
        if notificacion is None:
            raise ResourceNotFoundException("Notificación no encontrada.")

        if usuario_actual.id != notificacion.destinatario_id:
            raise BadRequestException("Esta notificación no le pertenece.")

        notificacion.estado = False

    def _obtener_tipo_notificacion(self, estado: EstadoSolicitud) -> TipoNotificacion:
        if estado == EstadoSolicitud.CANCELADA:
            return TipoNotificacion.CANCELACION
        return TipoNotificacion.CAMBIO_ESTADO

    def _obtener_contenido_notificacion(
        self, solicitud: SolicitudConsulta, motivo: str | None
    ) -> tuple[str, str]:
        if solicitud.estado_consulta == EstadoSolicitud.EN_PROCESO:
            return (
                "Solicitud aceptada",
                (
                    f"Tu solicitud de consulta {solicitud.numero_consulta} ha sido aceptada y "
                    "se encuentra actualmente en proceso de atención.\n"
                    f"La consulta está programada para el {solicitud.fecha_consulta} a las "
                    f"{solicitud.hora_consulta}."
                ),
            )
        if solicitud.estado_consulta == EstadoSolicitud.RECHAZADA:
            return (
                "Solicitud rechazada",
                (
                    f"Tu solicitud de consulta {solicitud.numero_consulta} ha sido rechazada.\n"
                    f"Motivo: {motivo}"
                ),
            )
        if solicitud.estado_consulta == EstadoSolicitud.CANCELADA:
            return (
                "Consulta cancelada",
                (
                    f"La consulta {solicitud.numero_consulta} ha sido cancelada.\n"
                    f"Motivo: {motivo}"
                ),
            )
        if solicitud.estado_consulta == EstadoSolicitud.RESUELTA:
            return (
                "Consulta resuelta",
                f"La consulta {solicitud.numero_consulta} ha sido marcada como resuelta.",
            )
        raise BadRequestException(
            f"No existe una notificación definida para el estado {solicitud.estado_consulta}."
        )