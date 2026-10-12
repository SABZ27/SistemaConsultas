from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.calificacion import calificacion_response
from app.models.calificacion_consulta import CalificacionConsulta
from app.models.enums import EstadoSolicitud
from app.models.usuario import Usuario
from app.repositories.calificacion_consulta import CalificacionConsultaRepository
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.solicitud_consulta import SolicitudConsultaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.calificacion import (
    CalificacionRequest,
    PromedioCalificacionesResponse,
)

NOMBRE_MODULO_GESTION = "GESTION_SOLICITUDES"


class CalificacionConsultaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CalificacionConsultaRepository(db)
        self.solicitud_repo = SolicitudConsultaRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.mxl_repo = ModuloXRolRepository(db)

    def calificar(self, id_solicitud: int, req: CalificacionRequest, usuario: Usuario):
        solicitud = self.solicitud_repo.find_by_id(id_solicitud)
        if solicitud is None:
            raise ResourceNotFoundException("Solicitud no encontrada.")

        if usuario.id != solicitud.estudiante_id:
            raise HTTPException(
                status_code=403,
                detail="Solo el estudiante dueño puede calificar la consulta.",
            )

        if solicitud.estado_consulta != EstadoSolicitud.RESUELTA:
            raise BadRequestException(
                "Solo se puede calificar una consulta con estado RESUELTA."
            )

        if self.repo.find_by_solicitud_id_and_estado_true(solicitud.id) is not None:
            raise BadRequestException("La consulta ya fue calificada.")

        calificacion = CalificacionConsulta(
            solicitud_id=solicitud.id,
            puntaje=req.puntaje,
            comentario=req.comentario,
        )
        self.repo.save(calificacion)
        return calificacion_response(calificacion)

    def obtener_por_solicitud(self, id_solicitud: int, usuario: Usuario):
        solicitud = self.solicitud_repo.find_by_id(id_solicitud)
        if solicitud is None:
            raise ResourceNotFoundException("Solicitud no encontrada.")

        es_participante = usuario.id in (solicitud.estudiante_id, solicitud.docente_id)
        if not es_participante and not self._tiene_gestion(usuario):
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para consultar la calificación.",
            )

        calificacion = self.repo.find_by_solicitud_id_and_estado_true(solicitud.id)
        if calificacion is None:
            raise ResourceNotFoundException("La consulta no ha sido calificada.")
        return calificacion_response(calificacion)

    def promedio_docente(self, id_docente: int):
        docente = self.user_repo.find_by_id_and_estado_true(id_docente)
        if docente is None:
            raise ResourceNotFoundException("Docente no encontrado.")
        promedio, total = self.repo.promedio_by_docente_id(docente.id)
        return PromedioCalificacionesResponse(
            docenteId=docente.id, promedio=round(promedio, 2), total=total
        )

    def _tiene_gestion(self, usuario: Usuario) -> bool:
        return self.mxl_repo.existe_permiso_activo(
            usuario.rol_id, NOMBRE_MODULO_GESTION
        )
