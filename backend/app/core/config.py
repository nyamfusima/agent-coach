"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Embeddings
    voyage_api_key: str = ""
    embedding_model: str = "voyage-3"
    embedding_dimensions: int = 1024

    # Database
    database_url: str = "postgresql://agentcoach:agentcoach@localhost:5432/agentcoach"

    # App
    env: str = "development"
    flows_dir: str = "../data/flows"
    knowledge_dir: str = "../data/knowledge"


@lru_cache
def get_settings() -> Settings:
    return Settings()
