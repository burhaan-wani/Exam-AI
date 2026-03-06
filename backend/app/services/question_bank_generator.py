import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from app.config import get_settings
from app.database import question_bank_collection, syllabus_collection, documents_collection
from app.models.schemas import BloomLevel, QuestionBankItem
from app.services.rag_retriever import build_retriever_for_unit

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_chat_model() -> ChatOpenAI:
    # Route LangChain OpenAI client through OpenRouter
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    return ChatOpenAI(model=settings.openrouter_model, temperature=0.3)


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

Bloom levels and counts:
- Level 1 (Remember/Understand): 3 questions
- Level 2 (Apply): 2 questions
- Level 3 (Analyze): 2 questions

If context is provided, base the questions on that material.

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "Question text here",
      "topic": "Subtopic or concept",
      "bloom_level": 1,
      "marks": 5,
      "difficulty": "easy|medium|hard"
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
    """
    For a given syllabus, use its topics/units and optional reference context
    (to be wired later) to generate a structured question bank.
    """
    syllabus = await syllabus_collection.find_one({"_id": ObjectId(syllabus_id)})
    if not syllabus:
        raise ValueError(f"Syllabus {syllabus_id} not found")

    topics = syllabus.get("topics", [])
    if not topics:
        raise ValueError("Syllabus has no extracted topics/units to generate from")

    units = []
    for t in topics:
        unit = t.get("unit") or t.get("name")
        if unit and unit not in units:
            units.append(unit)

    if not units:
        raise ValueError("Could not derive any course units from syllabus topics")

    llm = _get_chat_model()
    question_items: List[QuestionBankItem] = []

    # Build RAG retriever if reference documents exist for this syllabus
    ref_cursor = documents_collection.find({"syllabus_id": syllabus_id})
    ref_docs_raw = await ref_cursor.to_list(length=100)
    retriever = None
    if ref_docs_raw:
        lc_docs: List[Document] = []
        for d in ref_docs_raw:
            content = d.get("content", "")
            if not content:
                continue
            lc_docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "document_id": str(d["_id"]),
                        "file_name": d.get("file_name", ""),
                        "file_type": d.get("file_type", ""),
                    },
                )
            )
        if lc_docs:
            retriever = await build_retriever_for_unit(lc_docs)

    for unit_name in units:
        context_text = ""
        if retriever:
            docs = await retriever.ainvoke(unit_name)
            context_text = "\n\n".join(d.page_content for d in docs)

        prompt = QUESTION_BANK_TEMPLATE.format(unit_name=unit_name, context=context_text)

        def _run() -> str:
            resp = llm.invoke(prompt.to_messages())
            return resp.content or ""

        raw = await asyncio.to_thread(_run)

        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        try:
            data = json.loads(content)
            questions = data.get("questions", [])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse question bank JSON for unit %s: %s", unit_name, e)
            continue

        for q in questions:
            bloom_level_int = int(q.get("bloom_level", 1))
            if bloom_level_int == 1:
                bloom = BloomLevel.REMEMBER
            elif bloom_level_int == 2:
                bloom = BloomLevel.APPLY
            else:
                bloom = BloomLevel.ANALYZE

            doc = {
                "syllabus_id": syllabus_id,
                "question": q.get("question", ""),
                "unit": unit_name,
                "topic": q.get("topic", ""),
                "bloom_level": bloom.value,
                "marks": int(q.get("marks", 5)),
                "difficulty": q.get("difficulty", "medium"),
                "source_context": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            result = await question_bank_collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            question_items.append(
                QuestionBankItem(
                    id=str(result.inserted_id),
                    question=doc["question"],
                    unit=doc["unit"],
                    topic=doc["topic"],
                    bloom_level=bloom,
                    marks=doc["marks"],
                    difficulty=doc["difficulty"],
                    source_context=doc["source_context"],
                    created_at=doc["created_at"],
                )
            )

        logger.info("Generated %d questions for unit '%s'", len(questions), unit_name)

    return question_items

