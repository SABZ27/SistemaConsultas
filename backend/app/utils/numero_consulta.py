from datetime import date

from sqlalchemy.exc import IntegrityError

from app.exceptions.errors import BadRequestException
from app.models.solicitud_consulta import SolicitudConsulta
from app.repositories.solicitud_consulta import SolicitudConsultaRepository

MAX_INTENTOS = 5


def generar_numero_consulta(repo: SolicitudConsultaRepository) -> str:
    anio = date.today().year
    siguiente = repo.max_id() + 1
    return f"SC-{anio}-{siguiente:06d}"


def guardar_con_numero_unico(
    repo: SolicitudConsultaRepository, solicitud: SolicitudConsulta
) -> SolicitudConsulta:
    for _ in range(MAX_INTENTOS):
        solicitud.numero_consulta = generar_numero_consulta(repo)
        try:
            repo.db.add(solicitud)
            repo.db.flush()
            return solicitud
        except IntegrityError:
            repo.db.rollback()
    raise BadRequestException(
        "No se pudo generar un número de consulta único para la solicitud."
    )