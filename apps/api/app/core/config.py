from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="agentforge-api", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://agentforge:agentforge@127.0.0.1:5433/agentforge",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(
        default="agentforge_documents",
        alias="QDRANT_COLLECTION",
    )
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="qwen3:8b", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: float = Field(
        default=120.0,
        alias="OLLAMA_TIMEOUT_SECONDS",
    )
    document_storage_dir: Path = Field(
        default=ROOT_DIR / "storage" / "documents",
        alias="DOCUMENT_STORAGE_DIR",
    )
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="BACKEND_CORS_ORIGINS",
    )

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
