from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.enums import EnvironmentStrategy, StorageBackendStrategy
from src.core import path_conf


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables and defaults."""

    # FastAPI documentation settings
    FASTAPI_TITLE: str = "FastAPI"
    FASTAPI_SUMMARY: Optional[str] = None
    FASTAPI_DESCRIPTION: str = ""
    FASTAPI_VERSION: str = "0.1.0"
    FASTAPI_OPENAPI_URL: Optional[str] = "/openapi.json"
    FASTAPI_DOCS_URL: Optional[str] = "/docs"
    FASTAPI_REDOC_URL: Optional[str] = "/redoc"
    FASTAPI_TERMS_OF_SERVICE: Optional[str] = None
    FASTAPI_CONTACT: Optional[Dict[str, Union[str, Any]]] = None
    FASTAPI_LICENSE_INFO: Optional[Dict[str, Union[str, Any]]] = None

    # Environment & Debug
    ENVIRONMENT: EnvironmentStrategy = EnvironmentStrategy.LOCAL
    DEBUG: bool = True

    # Security & Authentication
    SECRET_KEY: str
    JWT_LIFETIME_SECONDS: int = 60 * 60 * 24  # 1 day

    # Hosts allowed in Host header validation
    ALLOWED_HOSTS: List[str]

    # CORS configuration
    CORS_ALLOWED_ORIGINS: List[str] = []
    CORS_ALLOWED_ORIGIN_REGEX: Optional[str] = None

    # i18n configuration
    SUPPORTED_LOCALES: List[str] = ["en", "az"]
    DEFAULT_LOCALE: str = "en"
    TIME_ZONE: str = "Asia/Baku"

    # Database
    DATABASE_URL: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_URL: str

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8

    # Email configuration
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_FROM: EmailStr

    # URLs & Routes
    BACKEND_URL: AnyHttpUrl
    FRONTEND_URL: AnyHttpUrl

    # Admin
    ADMIN_BASE_URL: str = "/admin"
    ADMIN_TITLE: str = "Admin"
    ADMIN_LOGO_URL: Optional[str] = f"{path_conf.STATIC_URL}assets/img/admin-logo.png"
    ADMIN_FAVICON_URL: Optional[str] = (
        f"{path_conf.STATIC_URL}assets/img/admin-favicon.png"
    )

    # Storage backend
    STORAGE_BACKEND_STRATEGY: StorageBackendStrategy = StorageBackendStrategy.LOCAL

    # Media CDN
    MEDIA_BASE_URL: Optional[AnyHttpUrl] = None

    # If True, old files will be automatically deleted
    # when they are replaced or the record is removed
    FILE_CLEANUP_ENABLED: bool = True

    # File upload configuration
    IMAGE_UPLOAD_ALLOWED_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings from environment variables or .env file.
    """
    return Settings()  # type: ignore[call-arg]


# Global singleton-like access
settings = get_settings()
