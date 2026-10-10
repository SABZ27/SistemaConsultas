from datetime import date

from app.repositories.solicitud_consulta import SolicitudConsultaRepository


def generar_numero_consulta(repo: SolicitudConsultaRepository) -> str:
    anio = date.today().year
    siguiente = repo.max_id() + 1
    return f"SC-{anio}-{siguiente:06d}"