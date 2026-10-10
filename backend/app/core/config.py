from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_secret: str = "REEMPLAZAR_POR_UN_SECRET_DE_AL_MENOS_32_CARACTERES"
    jwt_expiration_minutes: int = 30

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()