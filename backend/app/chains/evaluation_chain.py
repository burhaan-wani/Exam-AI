"""
LangChain Answer Evaluation Chain
Multi-step: rubric extraction → semantic scoring → completeness → Bloom alignment → aggregation
"""

import json
import logging
from langchain_openrouter import ChatOpenRouter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings
from app.services.prompt_builder import build_evaluation_prompt

logger = logging.getLogger(__name__)
settings = get_settings()


EVALUATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "You are an expert exam evaluator. Evaluate answers using rubric-based scoring. Return valid JSON only."),
    ("human", "{prompt}"),
])

RUBRIC_EXTRACTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at creating exam rubrics. Extract key evaluation criteria from the model answer."),
    ("human", """Given this exam question and model answer, extract a rubric with key points that should be present in a correct answer.

Question: {question_text}
Model Answer: {model_answer}
Max Marks: {max_marks}

Return ONLY valid JSON:
{{
  "rubric_points": [
    {{"point": "Key concept or fact", "weight": <float 0-1>}},
    ...
  ]
}}
"""),
])


def _get_llm():
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0.2,
    )


def _parse_json(text: str) -> dict:
    content = text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return json.loads(content)


async def extract_rubric(question_text: str, model_answer: str, max_marks: int) -> list[dict]:
    """Extract rubric points from model answer using LLM."""
    logger.info("Extracting rubric from model answer")
    chain = RUBRIC_EXTRACTION_TEMPLATE | _get_llm() | StrOutputParser()
    result = await chain.ainvoke({
        "question_text": question_text,
        "model_answer": model_answer,
        "max_marks": str(max_marks),
    })
    try:
        data = _parse_json(result)
        return data.get("rubric_points", [])
    except (json.JSONDecodeError, KeyError):
        logger.warning("Could not parse rubric, proceeding without it")
        return []


async def evaluate_answer(
    question_text: str,
    model_answer: str,
    student_answer: str,
    max_marks: int,
    bloom_level: str,
) -> dict:
    """Evaluate a student answer using the full evaluation chain."""
    logger.info(f"Evaluating answer for question (max_marks={max_marks})")

    # Step 1: Extract rubric (for internal use / logging)
    rubric = await extract_rubric(question_text, model_answer, max_marks)
    logger.info(f"Extracted {len(rubric)} rubric points")

    # Step 2: Full evaluation with scoring
    prompt_text = build_evaluation_prompt(
        question_text=question_text,
        model_answer=model_answer,
        student_answer=student_answer,
        max_marks=max_marks,
        bloom_level=bloom_level,
    )

    chain = EVALUATION_TEMPLATE | _get_llm() | StrOutputParser()
    result = await chain.ainvoke({"prompt": prompt_text})

    try:
        data = _parse_json(result)
        # Clamp awarded marks
        data["awarded_marks"] = min(float(data.get("awarded_marks", 0)), max_marks)
        data["awarded_marks"] = max(0.0, data["awarded_marks"])
        logger.info(f"Evaluation complete: {data['awarded_marks']}/{max_marks}")
        return data
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse evaluation output: {e}")
        raise ValueError(f"LLM returned invalid JSON during evaluation: {e}")
