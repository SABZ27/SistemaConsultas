from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.comentario import (
    ComentarioResponse,
    RegistroComentarioRequest,
    UpdateComentarioRequest,
)
from app.services.comentario import ComentarioService

router = APIRouter(prefix="/comentarios", tags=["Comentarios"])


@router.post("", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_comentario(
    req: RegistroComentarioRequest,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return ComentarioService(db).registrar(req, usuario)


@router.get("/solicitud/{solicitud_consulta_id}", response_model=list[ComentarioResponse])
def listar_comentarios_solicitud(
    solicitud_consulta_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return ComentarioService(db).listar_comentarios_por_solicitud(
        solicitud_consulta_id, usuario
    )


@router.get("/{id_comentario}", response_model=ComentarioResponse)
def obtener_comentario(
    id_comentario: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return ComentarioService(db).obtener_comentario_por_id(id_comentario, usuario)


@router.put("/{id_comentario}", response_model=ComentarioResponse)
def actualizar_comentario(
    id_comentario: int,
    req: UpdateComentarioRequest,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    return ComentarioService(db).actualizar(id_comentario, req, usuario)


@router.delete("/{id_comentario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comentario(
    id_comentario: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    ComentarioService(db).eliminar(id_comentario, usuario)