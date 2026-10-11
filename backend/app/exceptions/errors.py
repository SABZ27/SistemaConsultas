class ResourceNotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ServiceUnavailableException(Exception):
    def __init__(self, message: str = "Servicio de infraestructura no disponible"):
        super().__init__(message)
        self.message = message