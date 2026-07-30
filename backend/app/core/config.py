from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReleaseFlow API"
    database_url: str = "postgresql+psycopg://releaseflow:releaseflow@localhost:5432/releaseflow"
    cors_origins: str = "http://localhost:5173"
    jwt_secret: str = "development-only-insecure-secret"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    rate_limit_per_minute: int = 120
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle_seconds: int = 1800

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Render provides a generic PostgreSQL URL; SQLAlchemy needs the Psycopg 3 dialect."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def require_production_secret(self) -> "Settings":
        if self.cookie_secure and (
            self.jwt_secret == "development-only-insecure-secret" or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET must be a random value of at least 32 characters in production")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
