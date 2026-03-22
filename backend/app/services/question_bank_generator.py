import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings, get_text_model
from app.database import question_bank_collection, syllabus_collection
from app.models.schemas import BloomLevel, QuestionBankItem, QuestionReviewStatus
from app.services.rag_retriever import build_retriever_for_syllabus

logger = logging.getLogger(__name__)
settings = get_settings()
_BLOOM_CONFIG = {
    1: {"category": BloomLevel.REMEMBER, "difficulty": "Level 1", "paper_marks": 2},
    2: {"category": BloomLevel.APPLY, "difficulty": "Level 2", "paper_marks": 5},
    3: {"category": BloomLevel.ANALYZE, "difficulty": "Level 3", "paper_marks": 10},
}


def _get_chat_model() -> ChatOpenAI:
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    model_name = get_text_model(settings)
    return ChatOpenAI(model=model_name, temperature=0.3)


def _format_question_bank_item(doc: dict) -> QuestionBankItem:
    return QuestionBankItem(
        id=str(doc["_id"]),
        question=doc.get("question", ""),
        unit=doc.get("unit", ""),
        topic=doc.get("topic", ""),
        bloom_level=doc.get("bloom_level", "Remember"),
        marks=doc.get("marks", 0),
        difficulty=doc.get("difficulty", "Level 1"),
        status=doc.get("status", QuestionReviewStatus.PENDING.value),
        source_context=doc.get("source_context"),
        created_at=doc.get("created_at", ""),
    )


async def _build_context_text(syllabus_id: str, query_text: str) -> str:
    retriever = await build_retriever_for_syllabus(syllabus_id)
    if not retriever:
        return ""
    docs = await retriever.ainvoke(query_text)
    return "\n\n".join(doc.page_content for doc in docs)


async def generate_single_question(
    syllabus_id: str,
    unit_name: str,
    topic_name: str,
    bloom_level: int,
    previous_question: str | None = None,
) -> dict:
    bloom_config = _BLOOM_CONFIG.get(bloom_level, _BLOOM_CONFIG[1])
    bloom = bloom_config["category"]
    context_text = await _build_context_text(syllabus_id, f"{unit_name} {topic_name}")
    llm = _get_chat_model()

    previous_clause = ""
    if previous_question:
        previous_clause = f"\nAvoid repeating this previous question: {previous_question}"

    messages = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert exam question designer. Return ONLY valid JSON.",
            ),
            (
                "human",
                """Course unit: {unit_name}
Source topic: {topic_name}
Bloom level: {bloom_level}
Bloom category: {bloom_category}
Generate exactly one fresh question for this topic and Bloom level.
Keep the source topic exact and do not use course objectives or outcomes.{previous_clause}

Return ONLY valid JSON in this format:
{{
  "question": "Question text here",
  "topic": "{topic_name}",
  "bloom_level": {bloom_level},
  "bloom_category": "{bloom_category}"
}}

Context (may be empty):
{context}
""",
            ),
        ]
    ).format_messages(
        unit_name=unit_name,
        topic_name=topic_name,
        bloom_level=bloom_level,
        bloom_category=bloom.value,
        previous_clause=previous_clause,
        context=context_text,
    )

    def _run() -> str:
        resp = llm.invoke(messages)
        return resp.content or ""

    raw = await asyncio.to_thread(_run)
    content = raw.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    data = json.loads(content)
    return {
        "question": data.get("question", ""),
        "topic": data.get("topic") or topic_name,
        "bloom_level": bloom.value,
        "difficulty": bloom_config["difficulty"],
        "source_context": context_text[:1000] if context_text else None,
        "status": QuestionReviewStatus.PENDING.value,
    }


QUESTION_BANK_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert exam question designer. "
            "Generate exam questions for a university course. "
            "Always return ONLY valid JSON.",
        ),
        (
            "human",
            """Course unit: {unit_name}
Available sub-topics:
{topic_list}

Instructions:
- Ignore course objectives, outcomes, and prerequisites.
- Generate exactly 20 questions in total for this unit.
- Use only the listed sub-topics as source topics.
- Distribute the questions across these Bloom levels:
  - 7 questions for Level 1 (Remember)
  - 7 questions for Level 2 (Apply)
  - 6 questions for Level 3 (Analyze)
- Every question must include the exact source topic it came from.

If context is provided, base the questions on that material.

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "Question text here",
      "topic": "One of the listed sub-topics",
      "bloom_level": 1,
      "bloom_category": "Remember"
    }}
  ]
}}

Context (may be empty):
{context}
""",
        ),
    ]
)


async def generate_question_bank_for_syllabus(syllabus_id: str) -> List[QuestionBankItem]:
    """Generate a structured question bank using syllabus units and persistent RAG context."""
    syllabus = await syllabus_collection.find_one({"_id": ObjectId(syllabus_id)})
    if not syllabus:
        raise ValueError(f"Syllabus {syllabus_id} not found")

    syllabus_topics = syllabus.get("topics", [])
    if not syllabus_topics:
        raise ValueError("Syllabus has no extracted topics/units to generate from")

    unit_topics: list[tuple[str, list[str]]] = []
    for unit_record in syllabus_topics:
        unit_name = unit_record.get("unit") or unit_record.get("name")
        source_topics = unit_record.get("subtopics") or [unit_record.get("name", "")]
        source_topics = [topic for topic in source_topics if topic]
        if unit_name and source_topics:
            unit_topics.append((unit_name, source_topics))

    if not unit_topics:
        raise ValueError("Could not derive any topics from the syllabus units")

    llm = _get_chat_model()
    question_items: List[QuestionBankItem] = []
    await question_bank_collection.delete_many({"syllabus_id": syllabus_id})

    for unit_name, topic_names in unit_topics:
        context_text = await _build_context_text(syllabus_id, f"{unit_name} {' '.join(topic_names)}")

        messages = QUESTION_BANK_TEMPLATE.format_messages(
            unit_name=unit_name,
            topic_list="\n".join(f"- {topic}" for topic in topic_names),
            context=context_text,
        )

        def _run() -> str:
            resp = llm.invoke(messages)
            return resp.content or ""

        raw = await asyncio.to_thread(_run)
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        try:
            data = json.loads(content)
            questions = data.get("questions", [])[:20]
        except json.JSONDecodeError as error:
            logger.error("Failed to parse question bank JSON for unit %s: %s", unit_name, error)
            continue

        for question in questions:
            bloom_level_int = int(question.get("bloom_level", 1))
            bloom_config = _BLOOM_CONFIG.get(bloom_level_int, _BLOOM_CONFIG[1])
            bloom = bloom_config["category"]
            source_topic = question.get("topic") or topic_names[0]
            if source_topic not in topic_names:
                source_topic = topic_names[0]

            doc = {
                "syllabus_id": syllabus_id,
                "question": question.get("question", ""),
                "unit": unit_name,
                "topic": source_topic,
                "bloom_level": bloom.value,
                "marks": 0,
                "difficulty": bloom_config["difficulty"],
                "status": QuestionReviewStatus.PENDING.value,
                "source_context": context_text[:1000] if context_text else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            result = await question_bank_collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            question_items.append(_format_question_bank_item(doc))

        logger.info("Generated %d questions for unit '%s'", len(questions), unit_name)

    if not question_items:
        raise ValueError(
            "Question bank generation did not return any valid text questions. "
            "Check that OPENROUTER_MODEL is a chat-completions model that can return JSON."
        )

    return question_items
