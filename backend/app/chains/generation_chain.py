"""
LangChain Question Generation Chain
Multi-step chain: prompt building → LLM generation → JSON parsing
"""

import json
import logging
from langchain_openrouter import ChatOpenRouter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings
from app.services.prompt_builder import build_question_generation_prompt
from app.models.schemas import BloomLevel

logger = logging.getLogger(__name__)
settings = get_settings()


GENERATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "You are an expert exam question designer. Always return valid JSON only."),
    ("human", "{prompt}"),
])


def _get_llm():
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0.7,
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
    """Generate exam questions using LangChain chain."""
    logger.info(f"Generating {num_questions} questions: topic={topic}, bloom={bloom_level.value}, difficulty={difficulty}")

    prompt_text = build_question_generation_prompt(
        topic=topic,
        bloom_level=bloom_level,
        difficulty=difficulty,
        num_questions=num_questions,
        marks_per_question=marks_per_question,
    )

    chain = GENERATION_TEMPLATE | _get_llm() | StrOutputParser()
    result = await chain.ainvoke({"prompt": prompt_text})

    try:
        data = _parse_json(result)
        questions = data.get("questions", [])
        logger.info(f"Successfully generated {len(questions)} questions")
        return questions
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse generation output: {e}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
