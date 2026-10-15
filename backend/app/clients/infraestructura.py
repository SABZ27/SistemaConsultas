import logging

import httpx

from app.core.config import settings
from app.exceptions.errors import ServiceUnavailableException

logger = logging.getLogger("sistema_consultas")

# 1 intento + 1 reintento (el servicio puede estar dormido / arranque en frío).
INTENTOS = 2


class InfraestructuraClient:
    """Cliente HTTP del microservicio de infraestructura (Express + MySQL).

    Reenvía el Bearer del usuario. Un recurso inexistente (404) se representa
    como ``None``; los errores de red o las respuestas 5xx se traducen a un
    :class:`ServiceUnavailableException` (HTTP 503).

    El timeout se toma de ``INFRA_TIMEOUT`` (por defecto 60 s) para tolerar los
    arranques en frío del servicio en la nube.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        intentos: int = INTENTOS,
    ):
        self.base_url = (base_url or settings.infra_service_url).rstrip("/")
        self.timeout = settings.infra_timeout if timeout is None else timeout
        self.intentos = max(1, intentos)

    def obtener_recurso_fisico(self, id_recurso: int, token: str) -> dict | None:
        url = f"{self.base_url}/recursos-fisicos/{id_recurso}"
        respuesta = self._obtener(url, {"Authorization": f"Bearer {token}"})

        if respuesta.status_code == 404:
            return None
        if respuesta.status_code != 200:
            raise ServiceUnavailableException()
        return respuesta.json()

    def _obtener(self, url: str, headers: dict) -> httpx.Response:
        ultimo_error: Exception | None = None
        for _ in range(self.intentos):
            try:
                with httpx.Client(timeout=self.timeout) as cliente:
                    respuesta = cliente.get(url, headers=headers)
                if respuesta.status_code >= 500:
                    ultimo_error = ServiceUnavailableException()
                    continue
                return respuesta
            except httpx.HTTPError as error:
                logger.warning("Fallo al consultar infraestructura: %s", error)
                ultimo_error = ServiceUnavailableException()
        raise ultimo_error or ServiceUnavailableException()
