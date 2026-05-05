"""
Udyam Setu — Application Configuration
Reads environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised settings loaded from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ubiduser:ubidpass@postgres:5432/ubid_db"

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY: str = "supersecretkey123"

    # ── General ───────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Udyam Setu"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def async_database_url(self) -> str:
        """Return an asyncpg-compatible connection string."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Return a psycopg2-compatible connection string (Alembic, scripts)."""
        url = self.DATABASE_URL
        if "+asyncpg" in url:
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url


settings = Settings()
