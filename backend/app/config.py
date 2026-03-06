from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "exam_ai"
    openrouter_api_key: str = ""
    # Must be a chat/completions model (e.g. openai/gpt-3.5-turbo), NOT an embedding model
    openrouter_model: str = "openai/gpt-3.5-turbo"
    # Embedding model for RAG (must be an embeddings-capable model on OpenRouter)
    openrouter_embedding_model: str = "text-embedding-3-small"
    # Vector store backend: "chroma" (persistent) or "faiss" (in-memory)
    vector_store_backend: str = "chroma"
    # Local persistence dir for ChromaDB (relative to backend/ by default)
    chroma_persist_dir: str = "./data/chroma"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
