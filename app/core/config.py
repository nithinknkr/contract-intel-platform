from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    environment: str = "development"
    storage_base_dir: str = "./storage"
    redis_url: str = "redis://localhost:6379/0"
    chroma_url: str = "http://localhost:8001"

    # --- Auth (added in A4) ---
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # --- RAG Retrieval / LLM (added in B2) ---
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    top_k_vector: int = 15
    top_k_bm25: int = 15
    top_k_fused: int = 5
    rrf_k: int = 60


settings = Settings()