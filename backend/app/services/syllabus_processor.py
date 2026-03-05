import asyncio
import json
import logging
from openai import OpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_openai_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


async def extract_topics(syllabus_text: str) -> list[dict]:
    """Use OpenAI client (via OpenRouter) to extract topics from syllabus text."""
    logger.info("Extracting topics from syllabus text via LLM")

    system_message = (
        "You are an expert academic syllabus analyzer. "
        "Extract structured topics from the given syllabus text and return ONLY valid JSON."
    )
    user_message = f"""Analyze the following syllabus text and extract a structured list of topics.

For each topic, provide:
- name: the main topic name
- unit: the unit or module it belongs to (if identifiable)
- subtopics: a list of subtopics under it

Return ONLY valid JSON in this exact format:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "unit": "Unit 1",
      "subtopics": ["Subtopic A", "Subtopic B"]
    }}
  ]
}}

Syllabus text:
{syllabus_text[:8000]}
"""

    client = _get_openai_client()

    def _run_completion() -> str:
        resp = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        return resp.choices[0].message.content or ""

    try:
        raw_content = await asyncio.to_thread(_run_completion)
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        data = json.loads(content)
        return data.get("topics", [])
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to parse LLM topic extraction: {e}")
        # Fallback: split by lines as rough topics
        lines = [l.strip() for l in syllabus_text.split("\n") if l.strip() and len(l.strip()) > 5]
        return [{"name": line, "unit": "", "subtopics": []} for line in lines[:20]]
