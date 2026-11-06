from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

JWT_SECRET_MINIMO = 32
JWT_SECRET_EJEMPLO = "REEMPLAZAR_POR_UN_SECRET_DE_AL_MENOS_32_CARACTERES"
CORS_ORIGINS_EJEMPLO = "http://localhost:5173,http://localhost:3000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos
    db_url: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_username: str = "postgres"
    db_password: str = ""
    db_name: str = "sistema_consultas"

    # JWT
    jwt_secret: str = JWT_SECRET_EJEMPLO
    jwt_expiration_minutes: int = 30

    # CORS: lista separada por comas. No se permite '*'.
    cors_origins: str = CORS_ORIGINS_EJEMPLO

    # Administrador inicial (semilla)
    admin_correo: str = ""
    admin_password: str = ""
    admin_identificacion: str = ""

    # Servicio de infraestructura (Express + MySQL)
    infra_service_url: str = "http://localhost:3001"
    # Tiempo de espera (segundos) de las llamadas HTTP a infraestructura.
    # 60 s por defecto para tolerar arranques en frío (p. ej. Render).
    infra_timeout: float = 60.0

    @property
    def database_url(self) -> str:
        if not self.db_url:
            return (
                f"postgresql+psycopg://{self.db_username}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        url = self.db_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


def validar_jwt_secret(secreto: str) -> None:
    """Falla el arranque si el secreto no es seguro."""
    if len(secreto) < JWT_SECRET_MINIMO:
        raise RuntimeError(
            f"JWT_SECRET debe tener al menos {JWT_SECRET_MINIMO} caracteres."
        )
    if secreto == JWT_SECRET_EJEMPLO:
        raise RuntimeError("JWT_SECRET no puede ser el valor de ejemplo.")


def origenes_cors(cadena: str) -> list[str]:
    """Convierte CORS_ORIGINS en una lista y rechaza el comodín."""
    origenes: list[str] = []
    for origen in cadena.split(","):
        limpio = origen.strip().rstrip("/")
        if limpio:
            origenes.append(limpio)

    if not origenes:
        raise RuntimeError("CORS_ORIGINS debe definir al menos un origen.")
    if "*" in origenes:
        raise RuntimeError(
            "CORS_ORIGINS no puede contener '*' cuando se usan credenciales."
        )
    return origenes


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()