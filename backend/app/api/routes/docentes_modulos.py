from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import requiere_modulo
from app.db.session import get_db
from app.schemas.docente_modulo import AsignarDocenteModuloRequest, DocenteModuloResponse
from app.services.docente_modulo import DocenteModuloService

NOMBRE_MODULO = "ASIGNACION_DOCENTES"

router = APIRouter(prefix="/docentes-modulos", tags=["Docentes Módulos"])


@router.get("", response_model=list[DocenteModuloResponse])
def listar_docentes_modulos(
    incluir_inactivos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DocenteModuloService(db).listar(incluir_inactivos)


@router.post("", response_model=DocenteModuloResponse, status_code=status.HTTP_201_CREATED)
def asignar_docente_modulo(
    req: AsignarDocenteModuloRequest,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DocenteModuloService(db).asignar(req)


@router.get("/{id_asignacion}", response_model=DocenteModuloResponse)
def obtener_asignacion(
    id_asignacion: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DocenteModuloService(db).obtener_por_id(id_asignacion)


@router.patch("/{id_asignacion}/activar", response_model=DocenteModuloResponse)
def activar_asignacion(
    id_asignacion: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    return DocenteModuloService(db).activar(id_asignacion)


@router.delete("/{id_asignacion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(
    id_asignacion: int,
    db: Session = Depends(get_db),
    _usuario=Depends(requiere_modulo(NOMBRE_MODULO)),
):
    DocenteModuloService(db).eliminar(id_asignacion)
