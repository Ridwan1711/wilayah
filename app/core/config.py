from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Wilayah Indonesia API", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_url: str = Field(default="http://localhost:8000", alias="APP_URL")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    allowed_origins: str = Field(default="", alias="ALLOWED_ORIGINS")
    allowed_origin_regex: str | None = Field(default=None, alias="ALLOWED_ORIGIN_REGEX")
    cache_ttl_seconds: int = Field(default=86400, alias="CACHE_TTL_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
