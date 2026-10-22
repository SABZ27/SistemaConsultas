from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo, tiene_permiso_modulo
from app.db.session import get_db
from app.schemas.recurso_fisico import RecursoFisicoResponse
from app.schemas.zona import RegistroZonaRequest, UpdateZonaRequest, ZonaResponse
from app.services.recurso_fisico import RecursoFisicoService
from app.services.zona import ZonaService

NOMBRE_MODULO = "INFRAESTRUCTURA"

router = APIRouter(prefix="/zonas", tags=["Zonas"])


def _exigir_infraestructura(db: Session, usuario, incluir_inactivos: bool) -> None:
    if incluir_inactivos and not tiene_permiso_modulo(db, usuario, NOMBRE_MODULO):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para realizar esta acción.",
        )


@router.get("", response_model=list[ZonaResponse])
def listar_zonas(
    sedeId: int | None = None,
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    return ZonaService(db).listar_zonas(sedeId, incluirInactivos)


@router.post("", response_model=ZonaResponse, status_code=status.HTTP_201_CREATED)
def crear_zona(
    req: RegistroZonaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ZonaService(db).registrar(req)


@router.get("/{id_zona}", response_model=ZonaResponse)
def obtener_zona(
    id_zona: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return ZonaService(db).obtener_zona_por_id(id_zona)


@router.put("/{id_zona}", response_model=ZonaResponse)
def actualizar_zona(
    id_zona: int,
    req: UpdateZonaRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ZonaService(db).actualizar_zona(id_zona, req)


@router.delete("/{id_zona}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_zona(
    id_zona: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    ZonaService(db).desactivar_zona(id_zona)


@router.patch("/{id_zona}/activar", response_model=ZonaResponse)
def activar_zona(
    id_zona: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return ZonaService(db).activar_zona(id_zona)


@router.get("/{id_zona}/recursos-fisicos", response_model=list[RecursoFisicoResponse])
def listar_recursos_de_zona(
    id_zona: int,
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    ZonaService(db).obtener_zona_por_id(id_zona)
    return RecursoFisicoService(db).listar_recursos(
        zona_id=id_zona, incluir_inactivos=incluirInactivos
    )
