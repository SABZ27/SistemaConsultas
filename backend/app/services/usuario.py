from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.usuario import usuario_response
from app.models.usuario import Usuario
from app.repositories.programa_academico import ProgramaAcademicoRepository
from app.repositories.rol import RolRepository
from app.repositories.tipo_documento import TipoDocumentoRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import (
    DocenteResumen,
    RegistroUsuarioRequest,
    UpdateUsuarioRequest,
)
from app.core.security import hash_password


class UsuarioService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UsuarioRepository(db)
        self.prog_repo = ProgramaAcademicoRepository(db)
        self.rol_repo = RolRepository(db)
        self.tipo_doc_repo = TipoDocumentoRepository(db)

    def listar_usuarios(self, incluir_inactivos: bool = False):
        filas = self.user_repo.find_all() if incluir_inactivos else self.user_repo.find_all_by_estado_true()
        return [usuario_response(u) for u in filas]

    def obtener_usuario_por_id(self, id_usuario: int):
        usuario = self.user_repo.find_by_id_and_estado_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        return usuario_response(usuario)

    def crear_usuario(self, req: RegistroUsuarioRequest):
        if self.user_repo.find_by_correo_and_estado_true(req.correo) is not None:
            raise BadRequestException("El correo ya está registrado")
        if self.user_repo.find_by_identificacion_and_estado_true(req.identificacion) is not None:
            raise BadRequestException("La identificación ya está registrada.")

        rol = self.rol_repo.find_by_nombre_and_estado_true(req.rol.value)
        if rol is None:
            raise BadRequestException("El rol no existe.")

        programa = None
        if req.programaId is not None:
            programa = self.prog_repo.find_by_id(req.programaId)
            if programa is None:
                raise ResourceNotFoundException("Programa académico no encontrado")

        tipo_documento = self._resolver_tipo_documento(req.tipoDocumentoId)

        usuario = Usuario(
            identificacion=req.identificacion,
            nombre=req.nombre,
            apellido=req.apellido,
            correo=req.correo,
            password=hash_password(req.password),
            rol_id=rol.id,
            programa=programa,
            tipo_documento=tipo_documento,
        )
        self.user_repo.save(usuario)
        return usuario_response(usuario)

    def actualizar_usuario(self, id_usuario: int, req: UpdateUsuarioRequest):
        usuario = self.user_repo.find_by_id_and_estado_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")

        if usuario.correo != req.correo:
            usuario_con_correo = self.user_repo.find_by_correo_and_estado_true(req.correo)
            if usuario_con_correo is not None and usuario_con_correo.id != usuario.id:
                raise BadRequestException("El correo ya está registrado.")

        programa = None
        if req.programaId is not None:
            programa = self.prog_repo.find_by_id(req.programaId)
            if programa is None:
                raise ResourceNotFoundException("Programa académico no encontrado.")

        usuario.nombre = req.nombre
        usuario.apellido = req.apellido
        usuario.correo = req.correo
        usuario.programa = programa
        usuario.tipo_documento = self._resolver_tipo_documento(req.tipoDocumentoId)

        return usuario_response(usuario)

    def _resolver_tipo_documento(self, tipo_documento_id: int | None):
        if tipo_documento_id is None:
            return None
        tipo_documento = self.tipo_doc_repo.find_by_id_and_estado_true(tipo_documento_id)
        if tipo_documento is None:
            raise BadRequestException("El tipo de documento no es válido.")
        return tipo_documento

    def eliminar_usuario(self, id_usuario: int) -> None:
        usuario = self.user_repo.find_by_id_and_estado_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        usuario.estado = False

    def activar_usuario(self, id_usuario: int):
        usuario = self.user_repo.find_by_id(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        usuario.estado = True
        return usuario_response(usuario)

    def listar_docentes(self):
        return [
            DocenteResumen(id=u.id, nombre=u.nombre, apellido=u.apellido)
            for u in self.user_repo.find_docentes_activos()
        ]