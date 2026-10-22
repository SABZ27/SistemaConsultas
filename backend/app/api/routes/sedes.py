from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, requiere_modulo, tiene_permiso_modulo
from app.db.session import get_db
from app.schemas.recurso_fisico import RecursoFisicoResponse
from app.schemas.sede import RegistroSedeRequest, SedeResponse, UpdateSedeRequest
from app.schemas.zona import ZonaResponse
from app.services.recurso_fisico import RecursoFisicoService
from app.services.sede import SedeService
from app.services.zona import ZonaService

NOMBRE_MODULO = "INFRAESTRUCTURA"

router = APIRouter(prefix="/sedes", tags=["Sedes"])


def _exigir_infraestructura(db: Session, usuario, incluir_inactivos: bool) -> None:
    if incluir_inactivos and not tiene_permiso_modulo(db, usuario, NOMBRE_MODULO):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para realizar esta acción.",
        )


@router.get("", response_model=list[SedeResponse])
def listar_sedes(
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    return SedeService(db).listar_sedes(incluirInactivos)


@router.post("", response_model=SedeResponse, status_code=status.HTTP_201_CREATED)
def crear_sede(
    req: RegistroSedeRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return SedeService(db).registrar(req)


@router.get("/{id_sede}", response_model=SedeResponse)
def obtener_sede(
    id_sede: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    return SedeService(db).obtener_sede_por_id(id_sede)


@router.put("/{id_sede}", response_model=SedeResponse)
def actualizar_sede(
    id_sede: int,
    req: UpdateSedeRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return SedeService(db).actualizar_sede(id_sede, req)


@router.delete("/{id_sede}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_sede(
    id_sede: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    SedeService(db).desactivar_sede(id_sede)


@router.patch("/{id_sede}/activar", response_model=SedeResponse)
def activar_sede(
    id_sede: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return SedeService(db).activar_sede(id_sede)


@router.get("/{id_sede}/zonas", response_model=list[ZonaResponse])
def listar_zonas_de_sede(
    id_sede: int,
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    SedeService(db).obtener_sede_por_id(id_sede)
    return ZonaService(db).listar_zonas(id_sede, incluirInactivos)


@router.get("/{id_sede}/recursos-fisicos", response_model=list[RecursoFisicoResponse])
def listar_recursos_de_sede(
    id_sede: int,
    incluirInactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    _exigir_infraestructura(db, usuario, incluirInactivos)
    SedeService(db).obtener_sede_por_id(id_sede)
    return RecursoFisicoService(db).listar_recursos(
        sede_id=id_sede, incluir_inactivos=incluirInactivos
    )
