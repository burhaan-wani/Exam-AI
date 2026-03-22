from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "exam_ai"
    openrouter_api_key: str = ""
    # Text/chat model for syllabus processing, question bank generation, paper generation, and evaluation.
    openrouter_text_model: str = "openai/gpt-3.5-turbo"
    # Vision-capable model for scanned/image template parsing. Falls back to the text model if unset.
    openrouter_vision_model: str = ""
    # Backward-compatible legacy setting.
    openrouter_model: str = ""
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def ensure_chat_model_configured(model_name: str) -> str:
    normalized = (model_name or "").strip()
    if not normalized:
        raise ValueError(
            "OPENROUTER_MODEL is not set. Configure a chat-completions model such as "
            "'openai/gpt-3.5-turbo' in backend/.env."
        )

    lower_name = normalized.lower()
    if lower_name.startswith("sourceful/riverflow"):
        raise ValueError(
            f"OPENROUTER_MODEL='{normalized}' is an image-generation model, not a chat-completions model. "
            "Question bank generation expects text JSON output. Switch to a text/chat model such as "
            "'openai/gpt-3.5-turbo' or another OpenRouter chat model."
        )

    return normalized


def get_text_model(settings: Settings) -> str:
    candidate = settings.openrouter_text_model or settings.openrouter_model
    return ensure_chat_model_configured(candidate)


def get_vision_model(settings: Settings) -> str:
    candidate = settings.openrouter_vision_model or settings.openrouter_text_model or settings.openrouter_model
    return ensure_chat_model_configured(candidate)
