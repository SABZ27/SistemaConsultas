import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.servicios_externos import ServiciosExternosClient
from app.exceptions.errors import (
    BadRequestException,
    ResourceNotFoundException,
)
from app.mappers.solicitud_consulta import solicitud_consulta_response
from app.models.enums import EstadoSolicitud, Rol
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.usuario import Usuario
from app.repositories.disponibilidad_docente import DisponibilidadDocenteRepository
from app.repositories.docente_modulo import DocenteModuloRepository
from app.repositories.modulo import ModuloRepository
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.periodo_academico import PeriodoAcademicoRepository
from app.repositories.recurso_fisico import RecursoFisicoRepository
from app.repositories.solicitud_consulta import SolicitudConsultaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.solicitud import (
    AsignarRecursoFisicoRequest,
    CambiarEstadoSolicitudRequest,
    ReasignarDocenteRequest,
    RegistroSolicitudConsultaRequest,
    UpdateSolicitudConsultaRequest,
)
from app.services.email import CorreoPendiente
from app.services.evento_solicitud import EventoSolicitudService
from app.services.notificacion import NotificacionService
from app.services.recurso_fisico import ubicacion_recurso
from app.utils.numero_consulta import guardar_con_numero_unico

logger = logging.getLogger("sistema_consultas")

NOMBRE_MODULO_GESTION = "GESTION_SOLICITUDES"


class SolicitudConsultaService:
    def __init__(
        self,
        db: Session,
        cliente_externos: ServiciosExternosClient | None = None,
    ):
        self.db = db
        self.repo = SolicitudConsultaRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.modulo_repo = ModuloRepository(db)
        self.notificacion_service = NotificacionService(db)
        self.evento_service = EventoSolicitudService(db)
        self.mxl_repo = ModuloXRolRepository(db)
        self.docente_modulo_repo = DocenteModuloRepository(db)
        self.periodo_repo = PeriodoAcademicoRepository(db)
        self.disponibilidad_repo = DisponibilidadDocenteRepository(db)
        self.recurso_repo = RecursoFisicoRepository(db)
        self.cliente_externos = cliente_externos or ServiciosExternosClient()

    @property
    def correos_pendientes(self) -> list[CorreoPendiente]:
        """Correos que genera la operación (los envía la capa de API)."""
        return self.notificacion_service.correos_pendientes

    def registrar(
        self,
        req: RegistroSolicitudConsultaRequest,
        usuario_actual: Usuario,
        token: str,
    ):
        estudiante = self._obtener_estudiante(usuario_actual)
        docente = self._obtener_docente(req.docenteId)
        modulo = self._obtener_modulo(req.moduloId)

        self._validar_periodo_vigente(req.fechaConsulta)
        # El festivo se valida antes que la disponibilidad del docente para
        # que el mensaje que ve el estudiante sea claro.
        self._validar_festivo(req.fechaConsulta, token)
        self._validar_docente_asignado(docente.id, modulo.id)
        self._validar_disponibilidad(docente.id, req.fechaConsulta, req.horaConsulta)

        if req.fechaConsulta < date.today():
            raise BadRequestException(
                "La fecha de la consulta no puede ser anterior a la fecha actual."
            )

        solicitud = SolicitudConsulta(
            estado_consulta=EstadoSolicitud.PENDIENTE,
            prioridad=req.prioridad,
            asunto=req.asunto,
            descripcion=req.descripcion,
            fecha_consulta=req.fechaConsulta,
            hora_consulta=req.horaConsulta,
            estudiante=estudiante,
            docente=docente,
            modulo=modulo,
        )
        solicitud_guardada = guardar_con_numero_unico(self.repo, solicitud)

        self.notificacion_service.notificar_nueva_solicitud(solicitud_guardada, estudiante)
        self.evento_service.nueva_solicitud(solicitud_guardada, estudiante)

        return solicitud_consulta_response(solicitud_guardada)

    def obtener_por_id(self, id_solicitud: int, usuario_actual: Usuario):
        solicitud = self._obtener_solicitud(id_solicitud)
        if not self._es_participante(solicitud, usuario_actual) and not self._tiene_gestion(
            usuario_actual
        ):
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para consultar esta solicitud.",
            )
        return solicitud_consulta_response(solicitud)

    def listar_todas(self, usuario_actual: Usuario):
        if usuario_actual.rol == Rol.ESTUDIANTE:
            filas = self.repo.find_all_by_estudiante_id(usuario_actual.id)
        elif usuario_actual.rol == Rol.DOCENTE:
            filas = self.repo.find_all_by_docente_id(usuario_actual.id)
        else:
            if not self._tiene_gestion(usuario_actual):
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para consultar todas las solicitudes.",
                )
            filas = self.repo.find_all()
        return [solicitud_consulta_response(s) for s in filas]

    def actualizar(
        self,
        id_solicitud: int,
        req: UpdateSolicitudConsultaRequest,
        usuario_actual: Usuario,
        token: str,
    ):
        if req.fechaConsulta < date.today():
            raise BadRequestException(
                "La fecha de la consulta no puede ser anterior a la fecha actual."
            )

        solicitud = self._obtener_solicitud(id_solicitud)
        modulo = self._obtener_modulo(req.moduloId)
        fecha_anterior = solicitud.fecha_consulta
        hora_anterior = solicitud.hora_consulta
        destinatario = self._obtener_destinatario(solicitud, usuario_actual)

        if req.fechaConsulta != fecha_anterior:
            # Reprogramación: la nueva fecha tampoco puede ser festiva.
            self._validar_festivo(req.fechaConsulta, token)

        cambio_agenda = req.fechaConsulta != fecha_anterior or req.horaConsulta != hora_anterior
        if cambio_agenda and (req.motivo is None or req.motivo.strip() == ""):
            raise BadRequestException(
                "Debe indicar un motivo cuando se modifica la fecha o la hora de la consulta."
            )

        solicitud.prioridad = req.prioridad
        solicitud.asunto = req.asunto
        solicitud.descripcion = req.descripcion
        solicitud.fecha_consulta = req.fechaConsulta
        solicitud.hora_consulta = req.horaConsulta
        solicitud.modulo = modulo

        solicitud_guardada = self.repo.save(solicitud)

        if (
            solicitud_guardada.fecha_consulta != fecha_anterior
            or solicitud_guardada.hora_consulta != hora_anterior
        ):
            self.notificacion_service.notificar_cambio_agenda(
                solicitud_guardada, destinatario, req.motivo or "", usuario_actual
            )
            self.evento_service.cambio_agenda(solicitud_guardada, usuario_actual)

        return solicitud_consulta_response(solicitud_guardada)

    def asignar_recurso_fisico(
        self,
        id_solicitud: int,
        req: AsignarRecursoFisicoRequest,
        usuario_actual: Usuario,
    ):
        solicitud = self._obtener_solicitud(id_solicitud)

        if not self._validar_estado(solicitud):
            raise BadRequestException(
                "No se puede asignar un recurso físico a esta consulta."
            )

        if not self._tiene_gestion(usuario_actual) and usuario_actual.id != solicitud.docente_id:
            raise HTTPException(
                status_code=403,
                detail="Solo el docente asignado o un gestor pueden asignar recursos.",
            )

        recurso = self.recurso_repo.find_by_id(req.recursoFisicoId)
        if recurso is None:
            raise ResourceNotFoundException("Recurso físico no encontrado.")
        if not recurso.estado:
            raise BadRequestException("El recurso físico está inactivo.")

        solicitud.recurso_fisico_id = recurso.id
        solicitud.recurso_fisico_nombre = ubicacion_recurso(recurso)
        solicitud_guardada = self.repo.save(solicitud)

        self.notificacion_service.notificar_asignacion_recurso(
            solicitud_guardada, solicitud_guardada.estudiante, usuario_actual
        )
        self.evento_service.asignacion_recurso(solicitud_guardada, usuario_actual)

        return solicitud_consulta_response(solicitud_guardada)

    def cambiar_estado(
        self,
        id_solicitud: int,
        req: CambiarEstadoSolicitudRequest,
        usuario_actual: Usuario,
    ):
        solicitud = self._obtener_solicitud(id_solicitud)
        self._validar_actor_cambio_estado(solicitud, usuario_actual, req.estado)
        self._validar_cambio_estado(solicitud.estado_consulta, req.estado)
        self._validar_motivo(req.estado, req.motivo)

        solicitud.estado_consulta = req.estado
        solicitud_guardada = self.repo.save(solicitud)
        destinatario = self._obtener_destinatario(solicitud_guardada, usuario_actual)

        self.notificacion_service.notificar_cambio_estado(
            solicitud_guardada, destinatario, req.motivo, usuario_actual
        )
        self.evento_service.cambio_estado(solicitud_guardada, usuario_actual)

        return solicitud_consulta_response(solicitud_guardada)

    def reasignar_docente(
        self,
        id_solicitud: int,
        req: ReasignarDocenteRequest,
        usuario_actual: Usuario,
    ):
        solicitud = self._obtener_solicitud(id_solicitud)

        if not self._tiene_gestion(usuario_actual):
            raise HTTPException(
                status_code=403,
                detail="Solo un gestor de solicitudes puede reasignar docentes.",
            )

        if not self._validar_estado(solicitud):
            raise BadRequestException("No se puede reasignar esta consulta.")

        solicitud.docente = self._obtener_docente(req.docenteId)
        solicitud_guardada = self.repo.save(solicitud)

        self.notificacion_service.notificar_reasignacion(
            solicitud_guardada, solicitud_guardada.docente, usuario_actual
        )
        self.evento_service.reasignacion(solicitud_guardada, usuario_actual)

        return solicitud_consulta_response(solicitud_guardada)

    def eliminar(self, id_solicitud: int, usuario_actual: Usuario) -> None:
        solicitud = self._obtener_solicitud(id_solicitud)

        if not self._tiene_gestion(usuario_actual):
            raise HTTPException(
                status_code=403,
                detail="Solo un gestor de solicitudes puede eliminar solicitudes.",
            )

        solicitud.estado = False

    def _obtener_estudiante(self, usuario_actual: Usuario) -> Usuario:
        if usuario_actual.rol != Rol.ESTUDIANTE:
            raise BadRequestException("El usuario indicado no tiene el rol ESTUDIANTE.")
        return usuario_actual

    def _obtener_docente(self, id_docente: int) -> Usuario:
        usuario = self.user_repo.find_by_id_and_estado_true(id_docente)
        if usuario is None:
            raise ResourceNotFoundException("Docente no encontrado.")
        if usuario.rol != Rol.DOCENTE:
            raise BadRequestException("El usuario indicado no tiene el rol DOCENTE.")
        return usuario

    def _obtener_modulo(self, id_modulo: int):
        modulo = self.modulo_repo.find_by_id_and_estado_true(id_modulo)
        if modulo is None:
            raise ResourceNotFoundException("Módulo no encontrado.")
        return modulo

    def _validar_periodo_vigente(self, fecha: date) -> None:
        if self.periodo_repo.find_vigente(fecha) is None:
            raise BadRequestException(
                "La fecha de la consulta no corresponde a un periodo académico vigente."
            )

    def _validar_festivo(self, fecha: date, token: str) -> None:
        """Valida la fecha contra el servicio de festivos del microservicio.

        Si la fecha es festiva se rechaza la operación con 400. Si el servicio
        no está disponible la validación se omite (fail-open): la solicitud se
        registra igual y se deja un aviso en el log, sin nombres, correos ni
        identificadores.
        """
        try:
            respuesta = self.cliente_externos.validar_festivo(fecha, token)
        except Exception as error:  # fail-open: el servicio no debe tumbar la API
            codigo_http = getattr(error, "codigo_http", None)
            logger.warning(
                "No se pudo validar el carácter festivo de la fecha %s: %s%s",
                fecha.isoformat(),
                getattr(error, "causa", None) or type(error).__name__,
                (
                    f" (HTTP {codigo_http})"
                    if codigo_http in (401, 403)
                    else ""
                ),
            )
            return

        if not respuesta.get("esFestivo"):
            return

        raise BadRequestException(
            f"La fecha seleccionada es festivo: {respuesta.get('nombre') or 'Festivo'}"
        )

    def _validar_docente_asignado(self, id_docente: int, id_modulo: int) -> None:
        if not self.docente_modulo_repo.existe_asignacion(id_docente, id_modulo):
            raise BadRequestException(
                "El docente no está asignado al módulo indicado."
            )

    def _validar_disponibilidad(self, id_docente: int, fecha: date, hora) -> None:
        if not self.disponibilidad_repo.tiene_disponibilidad(
            id_docente, fecha.isoweekday(), hora
        ):
            raise BadRequestException(
                "El docente no tiene disponibilidad en el horario seleccionado."
            )

    def _obtener_solicitud(self, id_solicitud: int) -> SolicitudConsulta:
        solicitud = self.repo.find_by_id(id_solicitud)
        if solicitud is None:
            raise ResourceNotFoundException("Solicitud no encontrada.")
        return solicitud

    def _obtener_destinatario(self, solicitud: SolicitudConsulta, usuario_actual: Usuario) -> Usuario:
        if usuario_actual.id == solicitud.estudiante_id:
            return solicitud.docente
        if usuario_actual.id == solicitud.docente_id:
            return solicitud.estudiante
        return solicitud.docente

    def _es_participante(self, solicitud: SolicitudConsulta, usuario_actual: Usuario) -> bool:
        return (
            usuario_actual.id == solicitud.estudiante_id
            or usuario_actual.id == solicitud.docente_id
        )

    def _tiene_gestion(self, usuario_actual: Usuario) -> bool:
        return self.mxl_repo.existe_permiso_activo(
            usuario_actual.rol_id, NOMBRE_MODULO_GESTION
        )

    def _validar_actor_cambio_estado(
        self,
        solicitud: SolicitudConsulta,
        usuario_actual: Usuario,
        nuevo_estado: EstadoSolicitud,
    ) -> None:
        if self._tiene_gestion(usuario_actual):
            return
        if usuario_actual.id == solicitud.docente_id:
            return
        if usuario_actual.id == solicitud.estudiante_id:
            if nuevo_estado == EstadoSolicitud.CANCELADA:
                return
            raise HTTPException(
                status_code=403,
                detail="El estudiante solo puede cancelar su propia solicitud.",
            )
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para cambiar el estado de esta solicitud.",
        )

    def _validar_estado(self, solicitud: SolicitudConsulta) -> bool:
        return solicitud.estado_consulta in (EstadoSolicitud.EN_PROCESO, EstadoSolicitud.PENDIENTE)

    def _validar_motivo(self, estado: EstadoSolicitud, motivo: str | None) -> None:
        if estado in (EstadoSolicitud.RECHAZADA, EstadoSolicitud.CANCELADA):
            if motivo is None or motivo.strip() == "":
                raise BadRequestException(f"Debe indicar un motivo para {estado.value}.")

    def _validar_cambio_estado(
        self, estado_actual: EstadoSolicitud, nuevo_estado: EstadoSolicitud
    ) -> None:
        if estado_actual == nuevo_estado:
            raise BadRequestException(
                f"La solicitud ya se encuentra en estado {estado_actual.value}."
            )

        estados_permitidos = {
            EstadoSolicitud.PENDIENTE: {
                EstadoSolicitud.EN_PROCESO,
                EstadoSolicitud.RECHAZADA,
                EstadoSolicitud.CANCELADA,
            },
            EstadoSolicitud.EN_PROCESO: {
                EstadoSolicitud.RESUELTA,
                EstadoSolicitud.CANCELADA,
            },
            EstadoSolicitud.RECHAZADA: set(),
            EstadoSolicitud.CANCELADA: set(),
            EstadoSolicitud.RESUELTA: set(),
        }

        if nuevo_estado not in estados_permitidos.get(estado_actual, set()):
            raise BadRequestException(
                f"No se puede cambiar el estado de {estado_actual} a {nuevo_estado}"
            )