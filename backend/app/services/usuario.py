from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException, ResourceNotFoundException
from app.mappers.usuario import usuario_response
from app.repositories.programa_academico import ProgramaAcademicoRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import UpdateUsuarioRequest


class UsuarioService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UsuarioRepository(db)
        self.prog_repo = ProgramaAcademicoRepository(db)

    def listar_usuarios(self):
        return [
            usuario_response(u)
            for u in self.user_repo.find_all_by_activo_true()
        ]

    def obtener_usuario_por_id(self, id_usuario: int):
        usuario = self.user_repo.find_by_id_and_activo_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        return usuario_response(usuario)

    def actualizar_usuario(self, id_usuario: int, req: UpdateUsuarioRequest):
        usuario = self.user_repo.find_by_id_and_activo_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")

        if usuario.correo != req.correo:
            usuario_con_correo = self.user_repo.find_by_correo_and_activo_true(req.correo)
            if usuario_con_correo is not None and usuario_con_correo.id != usuario.id:
                raise BadRequestException("El correo ya está registrado.")

        programa = None
        if req.programaId is not None:
            programa = self.prog_repo.find_by_id(req.programaId)
            if programa is None:
                raise BadRequestException("El programa académico no existe.")

        usuario.nombre = req.nombre
        usuario.apellido = req.apellido
        usuario.correo = req.correo
        usuario.programa = programa

        return usuario_response(usuario)

    def eliminar_usuario(self, id_usuario: int) -> None:
        usuario = self.user_repo.find_by_id_and_activo_true(id_usuario)
        if usuario is None:
            raise ResourceNotFoundException("Usuario no encontrado.")
        usuario.activo = False