from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from typing import List
import json
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )
    # App
    APP_NAME: str = "Agentic Ticket System"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "changeme-in-production"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:80"
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ticket_user:ticket_pass@postgres:5432/ticket_db"
    DATABASE_SYNC_URL: str = "postgresql://ticket_user:ticket_pass@postgres:5432/ticket_db"
    # Redis
    REDIS_URL: str = "redis://:redis_pass@redis:6379/0"
    CELERY_BROKER_URL: str = "redis://:redis_pass@redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:redis_pass@redis:6379/2"
    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = "qdrant_secret"
    QDRANT_COLLECTION_TICKETS: str = "tickets"
    QDRANT_COLLECTION_KB: str = "knowledge_base"
    # MinIO
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_ROOT_USER: str = "minio_admin"
    MINIO_ROOT_PASSWORD: str = "minio_pass_123"
    MINIO_BUCKET_ATTACHMENTS: str = "ticket-attachments"
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MODEL_ADVANCED: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_REQUEST_TIMEOUT: int = 60
    # Embeddings (local BGE)
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    @property
    def allowed_origins_list(self) -> List[str]:
        v = self.ALLOWED_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [x.strip() for x in v.split(",") if x.strip()]
@lru_cache()
def get_settings() -> Settings:
    return Settings()
settings = get_settings()
