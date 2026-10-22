import logging
from datetime import date

import httpx

from app.core.config import settings
from app.exceptions.errors import ServiceUnavailableException

logger = logging.getLogger("sistema_consultas")

# La validación de festivos va en el camino crítico de la creación de la
# solicitud: usa un timeout corto (15 s) con 1 reintento.
TIMEOUT_FESTIVOS = 15.0
INTENTOS_GET = 2

# El envío de correo corre en segundo plano: usa el timeout general
# (INFRA_TIMEOUT, 60 s por defecto) y NO se reintenta, porque reenviar un
# correo puede duplicar el envío.
INTENTOS_POST = 1

PAIS_POR_DEFECTO = "CO"


class ServiciosExternosClient:
    """Cliente HTTP del microservicio Express de servicios externos.

    Reenvía el Bearer recibido. Los errores de red y las respuestas 5xx se
    traducen a :class:`ServiceUnavailableException` (HTTP 503), que conserva
    el código HTTP de la respuesta y el tipo de error de origen.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        timeout_festivos: float = TIMEOUT_FESTIVOS,
        intentos_get: int = INTENTOS_GET,
        intentos_post: int = INTENTOS_POST,
    ):
        self.base_url = (base_url or settings.infra_service_url).rstrip("/")
        self.timeout = settings.infra_timeout if timeout is None else timeout
        self.timeout_festivos = timeout_festivos
        self.intentos_get = max(1, intentos_get)
        self.intentos_post = max(1, intentos_post)

    # --- Festivos (GET, con reintento) -------------------------------------
    def validar_festivo(self, fecha: date, token: str) -> dict:
        url = f"{self.base_url}/festivos/validar"
        params = {"fecha": fecha.isoformat(), "pais": PAIS_POR_DEFECTO}
        respuesta = self._obtener(url, params, {"Authorization": f"Bearer {token}"})
        if respuesta.status_code != 200:
            raise ServiceUnavailableException(
                codigo_http=respuesta.status_code,
                causa="RespuestaHTTP",
            )
        return respuesta.json()

    # --- Correo (POST, sin reintento) --------------------------------------
    def enviar_correo(
        self,
        para: str,
        asunto: str,
        contenido: str,
        token: str,
        para_nombre: str | None = None,
    ) -> dict:
        url = f"{self.base_url}/correos"
        cuerpo = {"para": para, "asunto": asunto, "contenido": contenido}
        if para_nombre:
            cuerpo["paraNombre"] = para_nombre
        respuesta = self._enviar(url, cuerpo, {"Authorization": f"Bearer {token}"})
        if respuesta.status_code != 201:
            raise ServiceUnavailableException(
                codigo_http=respuesta.status_code,
                causa="RespuestaHTTP",
            )
        return respuesta.json()

    def _obtener(self, url: str, params: dict, headers: dict) -> httpx.Response:
        ultimo_error: Exception | None = None
        for _ in range(self.intentos_get):
            try:
                with httpx.Client(timeout=self.timeout_festivos) as cliente:
                    respuesta = cliente.get(url, params=params, headers=headers)
                if respuesta.status_code >= 500:
                    ultimo_error = ServiceUnavailableException(
                        codigo_http=respuesta.status_code,
                        causa="Respuesta5xx",
                    )
                    continue
                return respuesta
            except httpx.HTTPError as error:
                logger.warning(
                    "Fallo al consultar el servicio de servicios externos: %s",
                    type(error).__name__,
                )
                ultimo_error = ServiceUnavailableException(causa=type(error).__name__)
        raise ultimo_error or ServiceUnavailableException()

    def _enviar(self, url: str, cuerpo: dict, headers: dict) -> httpx.Response:
        for _ in range(self.intentos_post):
            try:
                with httpx.Client(timeout=self.timeout) as cliente:
                    return cliente.post(url, json=cuerpo, headers=headers)
            except httpx.HTTPError as error:
                logger.warning(
                    "Fallo al enviar el correo al servicio externo: %s",
                    type(error).__name__,
                )
                raise ServiceUnavailableException(causa=type(error).__name__) from error
        raise ServiceUnavailableException()
