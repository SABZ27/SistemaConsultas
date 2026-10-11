from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.comentario import comentario_response
from app.models.comentario import Comentario
from app.models.enums import EstadoSolicitud
from app.models.solicitud_consulta import SolicitudConsulta
from app.models.usuario import Usuario
from app.repositories.comentario import ComentarioRepository
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.solicitud_consulta import SolicitudConsultaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.comentario import (
    RegistroComentarioRequest,
    UpdateComentarioRequest,
)
from app.services.evento_solicitud import EventoSolicitudService
from app.services.notificacion import NotificacionService

NOMBRE_MODULO_GESTION = "GESTION_SOLICITUDES"


class ComentarioService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ComentarioRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.solicitud_repo = SolicitudConsultaRepository(db)
        self.notificacion_service = NotificacionService(db)
        self.evento_service = EventoSolicitudService(db)
        self.mxl_repo = ModuloXRolRepository(db)

    def registrar(self, req: RegistroComentarioRequest, autor: Usuario):
        consulta = self._obtener_solicitud(req.solicitudConsultaId)
        self._validar_participante(consulta, autor)

        if not self._puede_comentar(consulta):
            raise BadRequestException("No puede comentar esta consulta.")

        comentario = Comentario(
            contenido=req.contenido,
            autor=autor,
            solicitudConsulta=consulta,
        )
        comentario_guardado = self.repo.save(comentario)
        destinatario = self._obtener_destinatario(consulta, autor)

        self.notificacion_service.notificar_comentario(comentario_guardado, destinatario, autor)
        self.evento_service.nuevo_comentario(consulta, autor)

        return comentario_response(comentario_guardado)

    def obtener_comentario_por_id(self, id_comentario: int, usuario: Usuario):
        comentario = self.repo.find_by_id(id_comentario)
        if comentario is None:
            raise ResourceNotFoundException("Comentario no encontrado.")
        self._validar_participante(comentario.solicitudConsulta, usuario)
        return comentario_response(comentario)

    def actualizar(self, id_comentario: int, req: UpdateComentarioRequest, autor: Usuario):
        comentario = self.repo.find_by_id(id_comentario)
        if comentario is None:
            raise ResourceNotFoundException("Comentario no encontrado.")
        self._validar_autor(comentario, autor)

        if not self._puede_comentar(comentario.solicitudConsulta):
            raise BadRequestException("No puede actualizar comentarios en esta consulta.")

        comentario.contenido = req.contenido
        comentario.editado = True

        return comentario_response(self.repo.save(comentario))

    def listar_comentarios_por_solicitud(self, solicitud_id: int, usuario: Usuario):
        consulta = self._obtener_solicitud(solicitud_id)
        self._validar_participante(consulta, usuario)

        return [
            comentario_response(c)
            for c in self.repo.find_all_by_solicitud_id_order_fecha(solicitud_id)
        ]

    def eliminar(self, id_comentario: int, usuario: Usuario) -> None:
        comentario = self.repo.find_by_id(id_comentario)
        if comentario is None:
            raise ResourceNotFoundException("Comentario no encontrado.")
        es_autor = comentario.autor_id == usuario.id
        es_gestor = self.mxl_repo.existe_permiso_activo(usuario.rol_id, NOMBRE_MODULO_GESTION)
        if not es_autor and not es_gestor:
            raise HTTPException(
                status_code=403,
                detail="Solo el autor o un gestor de solicitudes puede eliminar este comentario.",
            )
        comentario.estado = False

    def _obtener_solicitud(self, id_solicitud: int) -> SolicitudConsulta:
        solicitud = self.solicitud_repo.find_by_id(id_solicitud)
        if solicitud is None:
            raise ResourceNotFoundException("Solicitud no encontrada.")
        return solicitud

    def _obtener_destinatario(self, consulta: SolicitudConsulta, autor: Usuario) -> Usuario:
        if autor.id == consulta.estudiante_id:
            return consulta.docente
        return consulta.estudiante

    def _validar_participante(self, consulta: SolicitudConsulta, usuario: Usuario) -> None:
        if usuario.id != consulta.estudiante_id and usuario.id != consulta.docente_id:
            raise BadRequestException("El usuario no pertenece a esta solicitud.")

    def _validar_autor(self, comentario: Comentario, usuario: Usuario) -> None:
        if comentario.autor_id != usuario.id:
            raise BadRequestException("Solo puedes editar tus propios comentarios.")

    def _puede_comentar(self, consulta: SolicitudConsulta) -> bool:
        return consulta.estado_consulta == EstadoSolicitud.EN_PROCESO