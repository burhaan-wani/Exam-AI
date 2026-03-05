"""
Question Refinement using OpenAI client (via OpenRouter)
Used in the HITL loop to refine questions based on teacher feedback.
"""

import asyncio
import json
import logging
from openai import OpenAI
from app.config import get_settings
from app.services.prompt_builder import build_refinement_prompt
from app.models.schemas import BloomLevel

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_openai_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


def _parse_json(text: str) -> dict:
    content = text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return json.loads(content)


async def refine_question(
    original_question: str,
    feedback: str,
    bloom_level: BloomLevel,
) -> dict:
    """Refine a question using OpenAI client based on teacher feedback."""
    logger.info(f"Refining question with feedback: {feedback[:80]}...")

    prompt_text = build_refinement_prompt(
        original_question=original_question,
        feedback=feedback,
        bloom_level=bloom_level,
    )

    client = _get_openai_client()

    def _run_completion() -> str:
        resp = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert exam question editor. Refine the question based on feedback. Return valid JSON only.",
                },
                {"role": "user", "content": prompt_text},
            ],
        )
        return resp.choices[0].message.content or ""

    try:
        raw = await asyncio.to_thread(_run_completion)
        data = _parse_json(raw)
        logger.info("Question refined successfully")
        return data
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse refinement output: {e}")
        raise ValueError(f"LLM returned invalid JSON during refinement: {e}")
