import logging
from dataclasses import dataclass

from app.clients.servicios_externos import ServiciosExternosClient
from app.core.security import crear_token_interno

logger = logging.getLogger("sistema_consultas")

# El microservicio Express limita el nombre del destinatario a 100 caracteres.
NOMBRE_MAXIMO = 100


@dataclass(frozen=True)
class CorreoPendiente:
    para: str
    asunto: str
    contenido: str
    para_nombre: str | None = None

    def nombre_truncado(self) -> str | None:
        if not self.para_nombre:
            return None
        return self.para_nombre[:NOMBRE_MAXIMO]


class EmailService:
    """Envía los correos al microservicio Express (que usa la API de Brevo).

    El envío es una operación de servicio a servicio: se firma un token
    interno con rol 'SERVICIO' (el mismo JWT_SECRET que el microservicio) y no
    se reenvía el token del usuario.

    El envío nunca propaga el error: si falla se registra una advertencia (sin
    dirección de correo ni contenido) y el flujo principal continúa.
    """

    def __init__(self, cliente: ServiciosExternosClient | None = None):
        self.cliente = cliente or ServiciosExternosClient()

    def enviar(self, correo: CorreoPendiente) -> bool:
        try:
            self.cliente.enviar_correo(
                para=correo.para,
                asunto=correo.asunto,
                contenido=correo.contenido,
                token=crear_token_interno(),
                para_nombre=correo.nombre_truncado(),
            )
        except Exception as error:  # el flujo principal no se rompe
            logger.warning(
                "No se pudo enviar el correo '%s' (%s)",
                correo.asunto,
                type(error).__name__,
            )
            return False
        return True
