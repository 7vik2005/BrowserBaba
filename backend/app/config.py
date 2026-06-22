from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "website_chunks"

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Models
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    embedding_model: str = "models/gemini-embedding-001"

    llm_model: str = "gemini-2.0-flash"

    # Retrieval
    top_k: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
