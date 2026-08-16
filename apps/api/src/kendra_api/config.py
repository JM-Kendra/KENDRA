"""Typed, environment-backed application configuration."""

from functools import cached_property
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Non-secret defaults and secret-safe runtime settings."""

    model_config = SettingsConfigDict(
        env_prefix="KENDRA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "test"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[AnyHttpUrl] = [AnyHttpUrl("http://127.0.0.1:3000")]
    readiness_timeout_seconds: float = Field(default=3.0, gt=0, le=30)

    postgres_host: str = "postgres"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_database: str = "kendra"
    postgres_user: str = "kendra"
    postgres_password: SecretStr = SecretStr("kendra-local-only-change-me")

    qdrant_url: AnyHttpUrl = AnyHttpUrl("http://qdrant:6333")
    qdrant_api_key: SecretStr | None = None
    ollama_url: AnyHttpUrl = AnyHttpUrl("http://ollama:11434")

    document_store_root: Path = Path("/documents")

    @field_validator("document_store_root")
    @classmethod
    def document_store_root_must_be_absolute(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("KENDRA_DOCUMENT_STORE_ROOT must be an absolute container path")
        return value

    @cached_property
    def postgres_dsn(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password.get_secret_value())
        database = quote_plus(self.postgres_database)
        return (
            f"postgresql://{user}:{password}@{self.postgres_host}:"
            f"{self.postgres_port}/{database}"
        )

    @property
    def qdrant_api_key_value(self) -> str | None:
        if self.qdrant_api_key is None:
            return None
        value = self.qdrant_api_key.get_secret_value()
        return value or None

    @property
    def cors_origin_values(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.cors_origins]
