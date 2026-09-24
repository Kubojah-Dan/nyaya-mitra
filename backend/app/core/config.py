from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "NyayaMitra API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(
        default="development-secret-key-32-bytes-long-for-local-runs-only",
        min_length=32,
        description="Cryptographic secret key for session verification",
    )

    # API Namespace
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://nyayamitra:nyayamitra_db_secret@localhost:5432/nyayamitra",
        description="PostgreSQL async connection string",
    )
    SQLITE_DB_PATH: str = "./nyayamitra.db"
    USE_SQLITE_FALLBACK: bool = True

    # Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600
    RATE_LIMIT_PER_MINUTE: int = 60

    # Privacy & Safety
    ENABLE_PII_REDACTION: bool = True
    STORAGE_DRIVER: str = "local"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    FILE_RETENTION_HOURS: int = 24

    # AI & Providers
    LLM_PROVIDER: str = "gemini"
    PRIMARY_MODEL: str = "gemini-2.0-flash"
    FALLBACK_MODEL: str = "llama3-70b-8192"  # Groq-hosted fallback
    FAST_MODEL: str = "gemini-2.0-flash-lite"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 384
    OCR_PROVIDER: str = "mock"

    # External Legal Source Adapters
    INDIA_CODE_BASE_URL: str = "https://www.indiacode.nic.in"
    ECOURTS_PORTAL_URL: str = "https://services.ecourts.gov.in"
    NALSA_PORTAL_URL: str = "https://nalsa.gov.in"
    TELE_LAW_URL: str = "https://www.tele-law.in"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def model_post_init(self, __context) -> None:
        if self.ENVIRONMENT == "production":
            if "development-secret-key" in self.SECRET_KEY:
                raise RuntimeError("SECRET_KEY must be securely configured in production environment.")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
