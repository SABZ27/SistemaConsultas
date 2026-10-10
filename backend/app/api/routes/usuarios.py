from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.usuario import UpdateUsuarioRequest, UsuarioResponse
from app.services.usuario import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return UsuarioService(db).listar_usuarios()


@router.get("/{id_usuario}", response_model=UsuarioResponse)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return UsuarioService(db).obtener_usuario_por_id(id_usuario)


@router.put("/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(
    id_usuario: int,
    req: UpdateUsuarioRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return UsuarioService(db).actualizar_usuario(id_usuario, req)


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    UsuarioService(db).eliminar_usuario(id_usuario)