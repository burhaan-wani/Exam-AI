"""
LangChain Question Refinement Chain
Used in the HITL loop to refine questions based on teacher feedback.
"""

import json
import logging
from langchain_openrouter import ChatOpenRouter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings
from app.services.prompt_builder import build_refinement_prompt
from app.models.schemas import BloomLevel

logger = logging.getLogger(__name__)
settings = get_settings()

REFINEMENT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "You are an expert exam question editor. Refine the question based on feedback. Return valid JSON only."),
    ("human", "{prompt}"),
])


def _get_llm():
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0.5,
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
    """Refine a question using LangChain chain based on teacher feedback."""
    logger.info(f"Refining question with feedback: {feedback[:80]}...")

    prompt_text = build_refinement_prompt(
        original_question=original_question,
        feedback=feedback,
        bloom_level=bloom_level,
    )

    chain = REFINEMENT_TEMPLATE | _get_llm() | StrOutputParser()
    result = await chain.ainvoke({"prompt": prompt_text})

    try:
        data = _parse_json(result)
        logger.info("Question refined successfully")
        return data
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse refinement output: {e}")
        raise ValueError(f"LLM returned invalid JSON during refinement: {e}")
