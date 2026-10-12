from pydantic import BaseModel, ConfigDict, Field


class AsignarDocenteModuloRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    docenteId: int
    moduloId: int


class DocenteModuloResponse(BaseModel):
    id: int
    docenteId: int
    nombreDocente: str
    moduloId: int
    nombreModulo: str
    estado: bool


class DocenteResumenModulo(BaseModel):
    id: int
    nombre: str
    apellido: str
