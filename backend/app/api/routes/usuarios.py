from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo
from app.db.session import get_db
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.schemas.usuario import (
    DocenteResumen,
    RegistroUsuarioRequest,
    UpdateUsuarioRequest,
    UsuarioResponse,
)
from app.services.usuario import UsuarioService

NOMBRE_MODULO_USUARIOS = "USUARIOS"

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _acceso_propio_o_modulo(usuario_id: int, usuario_actual, db: Session) -> None:
    if usuario_actual.id == usuario_id:
        return
    if not ModuloXRolRepository(db).existe_permiso_activo(
        usuario_actual.rol_id, NOMBRE_MODULO_USUARIOS
    ):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para gestionar usuarios.",
        )


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO_USUARIOS)),
):
    return UsuarioService(db).listar_usuarios(incluir_inactivos)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    req: RegistroUsuarioRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO_USUARIOS)),
):
    return UsuarioService(db).crear_usuario(req)


@router.get("/docentes", response_model=list[DocenteResumen])
def listar_docentes(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return UsuarioService(db).listar_docentes()


@router.get("/{id_usuario}", response_model=UsuarioResponse)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _acceso_propio_o_modulo(id_usuario, usuario, db)
    return UsuarioService(db).obtener_usuario_por_id(id_usuario)


@router.put("/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(
    id_usuario: int,
    req: UpdateUsuarioRequest,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _acceso_propio_o_modulo(id_usuario, usuario, db)
    return UsuarioService(db).actualizar_usuario(id_usuario, req)


@router.patch("/{id_usuario}/activar", response_model=UsuarioResponse)
def activar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO_USUARIOS)),
):
    return UsuarioService(db).activar_usuario(id_usuario)


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO_USUARIOS)),
):
    UsuarioService(db).eliminar_usuario(id_usuario)