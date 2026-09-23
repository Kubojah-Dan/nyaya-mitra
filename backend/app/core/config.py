from functools import lru_cache

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
    SECRET_KEY: str = "development-secret-key-change-in-production-min-32-bytes"

    # API Namespace
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nyayamitra:password@localhost:5432/nyayamitra"
    SQLITE_DB_PATH: str = "./nyayamitra.db"
    USE_SQLITE_FALLBACK: bool = True

    # Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 60

    # Privacy & Safety
    ENABLE_PII_REDACTION: bool = True
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    FILE_RETENTION_HOURS: int = 24

    # AI & Providers
    LLM_PROVIDER: str = "mock"
    PRIMARY_MODEL: str = "gemini-2.0-flash"
    FALLBACK_MODEL: str = "llama3-70b-8192"  # Groq-hosted fallback
    FAST_MODEL: str = "gemini-2.0-flash-lite"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "mock"
    OCR_PROVIDER: str = "mock"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
