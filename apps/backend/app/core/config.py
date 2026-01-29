from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.

    This centralizes application settings such as environment, database URLs,
    logging configuration, and API metadata.
    """

    # Pydantic Settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Core app metadata
    # -------------------------------------------------------------------------
    environment: Literal["dev", "test", "prod"] = Field(
        default="dev",
        alias="ENVIRONMENT",
    )
    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    project_name: str = Field(
        default="IoT Aquarium Monitoring Backend",
        alias="PROJECT_NAME",
    )
    project_description: str = Field(
        default="FastAPI backend for an IoT aquarium monitoring system.",
        alias="PROJECT_DESCRIPTION",
    )
    version: str = Field(
        default="0.1.0",
        alias="VERSION",
    )

    api_prefix: str = Field(
        default="/api",
        alias="API_PREFIX",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    storage_backend: Literal["memory", "sqlite", "mariadb"] = Field(
        default="sqlite",
        alias="STORAGE_BACKEND",
    )
    database_url: str = Field(
        default="sqlite:///./data/app.db",
        alias="DATABASE_URL",
    )
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_name: str = Field(default="aquarium", alias="DB_NAME")
    db_user: str = Field(default="aquarium_app", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )
    log_json: bool = Field(
        default=False,
        alias="LOG_JSON",
    )

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    # Raw string from env; we parse it manually to avoid JSON decoding issues.
    #
    # Examples:
    #   CORS_ORIGINS=*                                      -> ["*"]
    #   CORS_ORIGINS=http://localhost:3000                  -> ["http://localhost:3000"]
    #   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1 -> ["http://localhost:3000", "http://127.0.0.1"]
    cors_origins: str = Field(
        default="*",
        alias="CORS_ORIGINS",
    )
    allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    allow_methods: str = Field(default="*", alias="CORS_ALLOW_METHODS")
    allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")
    auth_token: str = Field(default="", alias="AUTH_TOKEN")
    demo_enabled: bool = Field(default=True, alias="DEMO_ENABLED")
    demo_username: str = Field(default="demo", alias="DEMO_USERNAME")
    demo_password: str = Field(default="password", alias="DEMO_PASSWORD")
    demo_user_id: str = Field(
        default="00000000-0000-0000-0000-000000000001",
        alias="DEMO_USER_ID",
    )
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expires_seconds: int = Field(default=3600, alias="JWT_EXPIRES_SECONDS")
    device_api_key_pepper: str = Field(default="change-me", alias="DEVICE_API_KEY_PEPPER")

    # -------------------------------------------------------------------------
    # SQLite durability/tuning
    # -------------------------------------------------------------------------
    sqlite_journal_mode: str = Field(default="WAL", alias="SQLITE_JOURNAL_MODE")
    sqlite_synchronous: str = Field(default="FULL", alias="SQLITE_SYNCHRONOUS")
    sqlite_busy_timeout_ms: int = Field(default=5000, alias="SQLITE_BUSY_TIMEOUT_MS")

    # -------------------------------------------------------------------------
    # Single-owner mode (self-hosting)
    # -------------------------------------------------------------------------
    single_owner_mode: bool = Field(default=False, alias="SINGLE_OWNER_MODE")
    owner_email: str = Field(default="", alias="OWNER_EMAIL")
    owner_user_id: str = Field(default="", alias="OWNER_USER_ID")

    # -------------------------------------------------------------------------
    # Rate limiting (simple in-memory)
    # -------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=120, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # -------------------------------------------------------------------------
    # SQLite backups (self-hosting)
    # -------------------------------------------------------------------------
    backup_enabled: bool = Field(default=True, alias="BACKUP_ENABLED")
    backup_dir: str = Field(default="backups", alias="BACKUP_DIR")
    backup_retention_days: int = Field(default=7, alias="BACKUP_RETENTION_DAYS")
    backup_interval_hours: int = Field(default=6, alias="BACKUP_INTERVAL_HOURS")

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Parsed CORS origins list derived from `cors_origins`.

        This is the value you should pass to FastAPI / CORSMiddleware.
        """
        raw = (self.cors_origins or "").strip()

        if not raw or raw == "*":
            return ["*"]

        if "," in raw:
            return [item.strip() for item in raw.split(",") if item.strip()]

        return [raw]

    @property
    def cors_methods_list(self) -> list[str]:
        if self.allow_methods == "*":
            return ["*"]
        return [m.strip() for m in self.allow_methods.split(",") if m.strip()]

    @property
    def cors_headers_list(self) -> list[str]:
        if self.allow_headers == "*":
            return ["*"]
        return [h.strip() for h in self.allow_headers.split(",") if h.strip()]

    @property
    def mariadb_async_url(self) -> str:
        return (
            "mariadb+asyncmy://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def mariadb_sync_url(self) -> str:
        return (
            "mariadb+pymysql://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached instance of application settings.

    Using `lru_cache` ensures that settings are loaded once, which avoids
    repeatedly parsing environment variables and the .env file.
    """
    return Settings()
