class ResourceNotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message