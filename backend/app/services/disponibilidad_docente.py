from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.disponibilidad import disponibilidad_response
from app.models.disponibilidad_docente import DisponibilidadDocente
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories.disponibilidad_docente import DisponibilidadDocenteRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.disponibilidad import (
    RegistroDisponibilidadRequest,
    UpdateDisponibilidadRequest,
)


class DisponibilidadDocenteService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DisponibilidadDocenteRepository(db)
        self.user_repo = UsuarioRepository(db)

    def listar(self, docente_id: int | None = None, incluir_inactivos: bool = False):
        if docente_id is not None:
            filas = (
                self.repo.find_all_by_docente_id(docente_id)
                if incluir_inactivos
                else self.repo.find_all_by_docente_id_and_estado_true(docente_id)
            )
        else:
            filas = (
                self.repo.find_all()
                if incluir_inactivos
                else self.repo.find_all_by_estado_true()
            )
        return [disponibilidad_response(d) for d in filas]

    def crear(self, req: RegistroDisponibilidadRequest, usuario: Usuario):
        docente_id = self._resolver_docente(req.docenteId, usuario)
        self._validar_horas(req.horaInicio, req.horaFin)

        existente = self.repo.find_by_docente_dia_hora(
            docente_id, req.diaSemana, req.horaInicio
        )
        if existente is not None and existente.estado:
            raise BadRequestException(
                "El docente ya tiene un tramo con esa hora de inicio ese día."
            )
        if self.repo.existe_solape(
            docente_id, req.diaSemana, req.horaInicio, req.horaFin
        ):
            raise BadRequestException(
                "El tramo se cruza con otra disponibilidad del docente ese día."
            )

        if existente is not None:
            existente.estado = True
            existente.hora_fin = req.horaFin
            return disponibilidad_response(existente)

        disponibilidad = DisponibilidadDocente(
            docente_id=docente_id,
            dia_semana=req.diaSemana,
            hora_inicio=req.horaInicio,
            hora_fin=req.horaFin,
        )
        self.repo.save(disponibilidad)
        return disponibilidad_response(disponibilidad)

    def obtener_por_id(self, id_: int, usuario: Usuario):
        disponibilidad = self._obtener_activa(id_)
        self._validar_propietario(disponibilidad, usuario)
        return disponibilidad_response(disponibilidad)

    def actualizar(self, id_: int, req: UpdateDisponibilidadRequest, usuario: Usuario):
        disponibilidad = self._obtener_activa(id_)
        self._validar_propietario(disponibilidad, usuario)
        self._validar_horas(req.horaInicio, req.horaFin)

        if self.repo.existe_solape(
            disponibilidad.docente_id,
            req.diaSemana,
            req.horaInicio,
            req.horaFin,
            excluir_id=disponibilidad.id,
        ):
            raise BadRequestException(
                "El tramo se cruza con otra disponibilidad del docente ese día."
            )

        disponibilidad.dia_semana = req.diaSemana
        disponibilidad.hora_inicio = req.horaInicio
        disponibilidad.hora_fin = req.horaFin
        return disponibilidad_response(disponibilidad)

    def eliminar(self, id_: int, usuario: Usuario) -> None:
        disponibilidad = self._obtener_activa(id_)
        self._validar_propietario(disponibilidad, usuario)
        disponibilidad.estado = False

    def activar(self, id_: int, usuario: Usuario):
        disponibilidad = self.repo.find_by_id(id_)
        if disponibilidad is None:
            raise ResourceNotFoundException("Disponibilidad no encontrada.")
        self._validar_propietario(disponibilidad, usuario)
        if self.repo.existe_solape(
            disponibilidad.docente_id,
            disponibilidad.dia_semana,
            disponibilidad.hora_inicio,
            disponibilidad.hora_fin,
            excluir_id=disponibilidad.id,
        ):
            raise BadRequestException(
                "El tramo se cruza con otra disponibilidad del docente ese día."
            )
        disponibilidad.estado = True
        return disponibilidad_response(disponibilidad)

    def _resolver_docente(self, docente_id: int | None, usuario: Usuario) -> int:
        if usuario.rol == Rol.ADMINISTRADOR:
            if docente_id is None:
                raise BadRequestException("Debe indicar el docente.")
            docente = self.user_repo.find_by_id_and_estado_true(docente_id)
            if docente is None:
                raise ResourceNotFoundException("Docente no encontrado.")
            if docente.rol != Rol.DOCENTE:
                raise BadRequestException("El usuario indicado no tiene el rol DOCENTE.")
            return docente.id

        if docente_id is not None and docente_id != usuario.id:
            raise HTTPException(
                status_code=403,
                detail="No puede gestionar la disponibilidad de otro docente.",
            )
        return usuario.id

    def _validar_propietario(
        self, disponibilidad: DisponibilidadDocente, usuario: Usuario
    ) -> None:
        if usuario.rol == Rol.ADMINISTRADOR:
            return
        if disponibilidad.docente_id != usuario.id:
            raise HTTPException(
                status_code=403,
                detail="No puede gestionar la disponibilidad de otro docente.",
            )

    def _validar_horas(self, hora_inicio, hora_fin) -> None:
        if hora_fin <= hora_inicio:
            raise BadRequestException(
                "La hora de fin debe ser posterior a la hora de inicio."
            )

    def _obtener_activa(self, id_: int) -> DisponibilidadDocente:
        disponibilidad = self.repo.find_by_id_and_estado_true(id_)
        if disponibilidad is None:
            raise ResourceNotFoundException("Disponibilidad no encontrada.")
        return disponibilidad
