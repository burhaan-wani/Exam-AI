from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "exam_ai"
    openrouter_api_key: str = ""
    # Must be a chat/completions model (e.g. openai/gpt-3.5-turbo), NOT an embedding model
    openrouter_model: str = "openai/gpt-3.5-turbo"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
