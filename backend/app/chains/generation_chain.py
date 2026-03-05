"""
Question Generation using OpenAI client (via OpenRouter)
Builds prompts with prompt_builder and parses JSON output.
"""

import asyncio
import json
import logging
from openai import OpenAI
from app.config import get_settings
from app.services.prompt_builder import build_question_generation_prompt
from app.models.schemas import BloomLevel

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_openai_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM output, handling code fences."""
    content = text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return json.loads(content)


async def generate_questions(
    topic: str,
    bloom_level: BloomLevel,
    difficulty: str,
    num_questions: int,
    marks_per_question: int,
) -> list[dict]:
    """Generate exam questions using OpenAI client (OpenRouter backend)."""
    logger.info(
        f"Generating {num_questions} questions: topic={topic}, "
        f"bloom={bloom_level.value}, difficulty={difficulty}"
    )

    prompt_text = build_question_generation_prompt(
        topic=topic,
        bloom_level=bloom_level,
        difficulty=difficulty,
        num_questions=num_questions,
        marks_per_question=marks_per_question,
    )

    client = _get_openai_client()

    def _run_completion() -> str:
        resp = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert exam question designer. Always return valid JSON only.",
                },
                {"role": "user", "content": prompt_text},
            ],
        )
        return resp.choices[0].message.content or ""

    try:
        raw = await asyncio.to_thread(_run_completion)
        data = _parse_json(raw)
        questions = data.get("questions", [])
        logger.info(f"Successfully generated {len(questions)} questions")
        return questions
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse generation output: {e}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
