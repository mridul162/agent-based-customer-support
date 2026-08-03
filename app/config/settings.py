from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Environment
    app_env: str = "development"

    # LLM Provider
    llm_provider: str = "OpenAI"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # RAG
    knowledge_base_path: str = "knowledge_base"
    rag_artifacts_path: str = "artifacts"
    chunk_artifacts_path: str = "artifacts/chunked"
    faiss_index_path: str = "artifacts/embeddings/index.faiss"
    faiss_metadata_path: str = "artifacts/embeddings/metadata.json"
    manifest_path: str = "artifacts/embeddings/manifest.json"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "customer_support"
    postgres_user: str = "postgres"
    postgres_password: str = "password"

    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return (
            f"postgresql+psycopg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    # API
    API_BASE_URL: str = "http://localhost:8000"  # Default value, can be overridden by environment variable


settings = Settings()  # type: ignore[arg-type]
