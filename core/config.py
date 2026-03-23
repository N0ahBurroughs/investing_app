from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/investing"
    gemini_api_key: str | None = None
    market_poll_seconds: int = 30
    log_level: str = "INFO"


settings = Settings()
