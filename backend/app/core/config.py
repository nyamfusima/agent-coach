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

    # CORS: comma-separated production frontend origins allowed to call the API.
    # localhost (any port) is always allowed for local dev; this adds deployed ones.
    cors_origins: str = "https://agent-coach-topaz.vercel.app"
    # Also allow any https://<name>.vercel.app origin (covers Vercel previews).
    cors_allow_vercel: bool = True

    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def missing_ai_keys(self) -> list[str]:
        """Names of required AI API keys that are unset/empty."""
        missing = []
        if not self.anthropic_api_key.strip():
            missing.append("ANTHROPIC_API_KEY")
        if not self.voyage_api_key.strip():
            missing.append("VOYAGE_API_KEY")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
