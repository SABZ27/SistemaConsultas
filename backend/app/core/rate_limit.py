"""Limitador de intentos en memoria.

Es local al proceso: se reinicia al reiniciar el servicio y no se comparte
entre instancias. Se usa para frenar fuerza bruta y abuso de los endpoints de
autenticación sin añadir una dependencia externa (Redis, etc.).

Todos los valores numéricos de los límites viven en este archivo.
"""

import ipaddress
import logging
import math
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Callable

from fastapi import Request

from app.core.config import settings

logger = logging.getLogger("sistema_consultas.ip")

# Tope global de claves por limitador. Evita crecimiento sin control si un
# atacante varía correos o IPs.
MAX_CLAVES_LIMITADOR = 10_000

# Login: bloqueo de la pareja (correo + IP) tras 5 fallos.
LOGIN_PAR_MAX_FALLOS = 5
LOGIN_PAR_VENTANA_SEGUNDOS = 15 * 60
LOGIN_PAR_BLOQUEO_SEGUNDOS = 15 * 60

# Login: límite más alto solo por correo para ataques distribuidos.
LOGIN_CORREO_MAX_FALLOS = 15
LOGIN_CORREO_VENTANA_SEGUNDOS = 15 * 60

# Login: límite solo por IP. No se limpia con un login correcto.
# Más alto que el de pareja (5) y el de correo (15) para mitigar el riesgo de
# agrupar muchos clientes tras el edge cuando TRUSTED_PROXY_HOPS no es exacto.
LOGIN_IP_MAX_FALLOS = 100
LOGIN_IP_VENTANA_SEGUNDOS = 15 * 60
LOGIN_IP_BLOQUEO_SEGUNDOS = 15 * 60

# Registro público.
REGISTRO_IP_MAX_SOLICITUDES = 10
REGISTRO_IP_VENTANA_SEGUNDOS = 60 * 60
REGISTRO_CORREO_MAX_SOLICITUDES = 5
REGISTRO_CORREO_VENTANA_SEGUNDOS = 60 * 60

# Recuperación de contraseña.
FORGOT_IP_MAX_SOLICITUDES = 10
FORGOT_IP_VENTANA_SEGUNDOS = 15 * 60
FORGOT_CORREO_MAX_SOLICITUDES = 3
FORGOT_CORREO_VENTANA_SEGUNDOS = 15 * 60

# Restablecimiento de contraseña.
RESET_IP_MAX_SOLICITUDES = 10
RESET_IP_VENTANA_SEGUNDOS = 15 * 60
RESET_TOKEN_MAX_SOLICITUDES = 5
RESET_TOKEN_VENTANA_SEGUNDOS = 15 * 60

MENSAJE_DEMASIADAS_SOLICITUDES = (
    "Demasiadas solicitudes. Intenta de nuevo más tarde."
)
MENSAJE_DEMASIADOS_INTENTOS = (
    "Demasiados intentos fallidos. Intenta de nuevo en 15 minutos."
)


@dataclass(frozen=True)
class ResultadoLimite:
    permitido: bool
    reintentar_en: int = 0


@dataclass
class _Entrada:
    eventos: list[float] = field(default_factory=list)
    ultimo: float = 0.0
    bloqueado_hasta: float = 0.0


class RateLimiter:
    """Ventana deslizante con bloqueo opcional y purga de claves vencidas."""

    def __init__(
        self,
        maximo: int,
        ventana_segundos: int,
        bloqueo_segundos: int = 0,
        max_claves: int = MAX_CLAVES_LIMITADOR,
        reloj: Callable[[], float] = time.monotonic,
    ):
        self.maximo = maximo
        self.ventana_segundos = ventana_segundos
        self.bloqueo_segundos = bloqueo_segundos
        self.max_claves = max_claves
        self.reloj = reloj
        self._datos: dict[str, _Entrada] = {}
        self._lock = Lock()

    @property
    def claves_actuales(self) -> int:
        with self._lock:
            return len(self._datos)

    def permitir(self, clave: str) -> ResultadoLimite:
        """Registra una solicitud si hay cupo en la ventana."""
        with self._lock:
            ahora = self.reloj()
            entrada = self._obtener(clave, ahora, crear=True)
            if entrada is None:
                return ResultadoLimite(True, 0)

            if entrada.bloqueado_hasta > ahora:
                return ResultadoLimite(
                    False, self._segundos(entrada.bloqueado_hasta - ahora)
                )

            self._recortar(entrada, ahora)
            if len(entrada.eventos) >= self.maximo:
                return ResultadoLimite(
                    False, self._segundos(entrada.eventos[0] + self.ventana_segundos - ahora)
                )

            entrada.eventos.append(ahora)
            entrada.ultimo = ahora
            return ResultadoLimite(True, 0)

    def esta_bloqueado(self, clave: str) -> ResultadoLimite:
        """Consulta sin consumir cupo."""
        with self._lock:
            ahora = self.reloj()
            entrada = self._obtener(clave, ahora, crear=False)
            if entrada is None:
                return ResultadoLimite(True, 0)

            if entrada.bloqueado_hasta > ahora:
                return ResultadoLimite(
                    False, self._segundos(entrada.bloqueado_hasta - ahora)
                )

            self._recortar(entrada, ahora)
            if len(entrada.eventos) >= self.maximo:
                return ResultadoLimite(
                    False, self._segundos(entrada.eventos[0] + self.ventana_segundos - ahora)
                )

            return ResultadoLimite(True, 0)

    def registrar_fallo(self, clave: str) -> None:
        """Registra un fallo y aplica bloqueo si se alcanza el máximo."""
        with self._lock:
            ahora = self.reloj()
            entrada = self._obtener(clave, ahora, crear=True)
            if entrada is None or entrada.bloqueado_hasta > ahora:
                return

            self._recortar(entrada, ahora)
            entrada.eventos.append(ahora)
            entrada.ultimo = ahora

            if (
                self.bloqueo_segundos > 0
                and len(entrada.eventos) >= self.maximo
            ):
                entrada.bloqueado_hasta = ahora + self.bloqueo_segundos
                entrada.eventos.clear()

    def limpiar(self, clave: str) -> None:
        with self._lock:
            self._datos.pop(clave, None)

    def reiniciar(self) -> None:
        with self._lock:
            self._datos.clear()

    def _obtener(
        self, clave: str, ahora: float, *, crear: bool
    ) -> _Entrada | None:
        entrada = self._datos.get(clave)
        if entrada is not None:
            self._recortar(entrada, ahora)
            if entrada.bloqueado_hasta <= ahora and not entrada.eventos:
                del self._datos[clave]
                entrada = None

        if entrada is None and crear:
            self._asegurar_capacidad(ahora)
            entrada = _Entrada(ultimo=ahora)
            self._datos[clave] = entrada

        return entrada

    def _recortar(self, entrada: _Entrada, ahora: float) -> None:
        limite = ahora - self.ventana_segundos
        while entrada.eventos and entrada.eventos[0] <= limite:
            entrada.eventos.pop(0)

    def _asegurar_capacidad(self, ahora: float) -> None:
        if len(self._datos) < self.max_claves:
            return

        self._purgar_vencidas(ahora)
        while len(self._datos) >= self.max_claves:
            clave_vieja = min(
                self._datos, key=lambda clave: self._datos[clave].ultimo
            )
            del self._datos[clave_vieja]

    def _purgar_vencidas(self, ahora: float) -> None:
        for clave in list(self._datos):
            entrada = self._datos[clave]
            self._recortar(entrada, ahora)
            if entrada.bloqueado_hasta <= ahora and not entrada.eventos:
                del self._datos[clave]

    @staticmethod
    def _segundos(segundos: float) -> int:
        return max(1, math.ceil(segundos))


LIMITE_LOGIN_PAR = RateLimiter(
    LOGIN_PAR_MAX_FALLOS,
    LOGIN_PAR_VENTANA_SEGUNDOS,
    LOGIN_PAR_BLOQUEO_SEGUNDOS,
)
LIMITE_LOGIN_CORREO = RateLimiter(
    LOGIN_CORREO_MAX_FALLOS,
    LOGIN_CORREO_VENTANA_SEGUNDOS,
)
LIMITE_LOGIN_IP = RateLimiter(
    LOGIN_IP_MAX_FALLOS,
    LOGIN_IP_VENTANA_SEGUNDOS,
    LOGIN_IP_BLOQUEO_SEGUNDOS,
)
LIMITE_REGISTRO_IP = RateLimiter(
    REGISTRO_IP_MAX_SOLICITUDES,
    REGISTRO_IP_VENTANA_SEGUNDOS,
)
LIMITE_REGISTRO_CORREO = RateLimiter(
    REGISTRO_CORREO_MAX_SOLICITUDES,
    REGISTRO_CORREO_VENTANA_SEGUNDOS,
)
LIMITE_FORGOT_IP = RateLimiter(
    FORGOT_IP_MAX_SOLICITUDES,
    FORGOT_IP_VENTANA_SEGUNDOS,
)
LIMITE_FORGOT_CORREO = RateLimiter(
    FORGOT_CORREO_MAX_SOLICITUDES,
    FORGOT_CORREO_VENTANA_SEGUNDOS,
)
LIMITE_RESET_IP = RateLimiter(
    RESET_IP_MAX_SOLICITUDES,
    RESET_IP_VENTANA_SEGUNDOS,
)
LIMITE_RESET_TOKEN = RateLimiter(
    RESET_TOKEN_MAX_SOLICITUDES,
    RESET_TOKEN_VENTANA_SEGUNDOS,
)

_LIMITADORES = (
    LIMITE_LOGIN_PAR,
    LIMITE_LOGIN_CORREO,
    LIMITE_LOGIN_IP,
    LIMITE_REGISTRO_IP,
    LIMITE_REGISTRO_CORREO,
    LIMITE_FORGOT_IP,
    LIMITE_FORGOT_CORREO,
    LIMITE_RESET_IP,
    LIMITE_RESET_TOKEN,
)


def reiniciar_limitadores() -> None:
    for limitador in _LIMITADORES:
        limitador.reiniciar()


def _normalizar_ip(valor: str | None) -> str | None:
    if not valor:
        return None
    try:
        return str(ipaddress.ip_address(valor.strip()))
    except ValueError:
        return None


def _host_directo(request: Request) -> str:
    host = request.client.host if request.client else None
    return _normalizar_ip(host) or "desconocida"


def obtener_ip(request: Request) -> str:
    """IP del cliente contando los proxies de confianza desde la derecha.

    X-Forwarded-For puede venir como "cliente, edge". Con
    TRUSTED_PROXY_HOPS=1 la entrada -(1+1) es el cliente y la última (el edge)
    se descarta. Las entradas a la izquierda del cliente son falsificables y
    se ignoran. Si falta el encabezado, tiene menos entradas de las esperadas
    o CUALQUIERA de sus entradas está vacía, malformada o no es una IP válida,
    se usa la conexión directa.
    """
    reenviado = request.headers.get("x-forwarded-for")
    partes = (
        [parte.strip() for parte in reenviado.split(",")]
        if reenviado is not None
        else []
    )

    if settings.diagnostico_ip:
        # Solo conteos y booleanos: nunca valores de IP.
        logger.info(
            "Diagnostico IP: x_forwarded_for_entradas=%d true_client_ip=%s",
            len(partes),
            "true-client-ip" in request.headers,
        )

    hops = settings.trusted_proxy_hops
    if len(partes) < hops + 1:
        return _host_directo(request)

    ips = []
    for parte in partes:
        ip = _normalizar_ip(parte)
        if ip is None:
            return _host_directo(request)
        ips.append(ip)

    return ips[-(hops + 1)]
