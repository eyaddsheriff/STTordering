# ═══════════════════════════════════════════════
# core/config.py — Pydantic Settings
# ═══════════════════════════════════════════════

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars not defined here
    )

    # ─── App ───
    app_name: str = "Voice Ordering API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # ─── Database ───
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "voice_ordering"
    db_user: str = "voice_user"
    db_password: str = "voice_pass_2026"

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ─── Redis ───
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = "redis_pass_2026"

    @property
    def redis_url(self) -> str:
        """Redis connection string."""
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    # ─── API ───
    api_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ─── Sync ───
    sync_interval_minutes: int = 15
    restaurant_engine_base_url: str = ""
    restaurant_engine_api_key: str = ""

    # ─── CORS ───
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ─── Security (Placeholder) ───
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere."""
    return Settings()
