class ResourceNotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestException(Exception):
    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors


class ServiceUnavailableException(Exception):
    def __init__(
        self,
        message: str = "Servicio de infraestructura no disponible",
        codigo_http: int | None = None,
        causa: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        # Código HTTP que respondió el servicio externo (si hubo respuesta).
        self.codigo_http = codigo_http
        # Tipo de error de origen (por ejemplo "ConnectError").
        self.causa = causa


class TooManyRequestsException(Exception):
    def __init__(
        self,
        message: str = "Demasiadas solicitudes. Intenta de nuevo más tarde.",
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class EsquemaAnteriorError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AdminPasswordError(RuntimeError):
    """La contraseña del administrador inicial no cumple la política."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message