from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Environment
    app_env: str

    # LLM Provider
    llm_provider: str = "OpenAI"

    # OpenAI
    openai_api_key: str
    openai_model: str
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
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )


settings = Settings() # type: ignore
