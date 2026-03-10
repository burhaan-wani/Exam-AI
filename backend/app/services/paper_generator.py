import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.database import question_bank_collection, final_question_paper_collection
from app.models.schemas import QuestionPaperTemplate, PaperQuestion

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_chat_model() -> ChatOpenAI:
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    return ChatOpenAI(model=settings.openrouter_model, temperature=0.2)


PAPER_SELECTION_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert exam setter. "
            "You are given a question bank and a paper template. "
            "Select questions from the bank to build the paper. "
            "Do NOT invent new questions. Always return ONLY valid JSON.",
        ),
        (
            "human",
            """Question bank (JSON list of questions with 'id', 'unit', 'bloom_level', 'marks'):
{question_bank}

Paper template (sections with bloom level and required question count):
{template}

Return ONLY valid JSON in this format:
{{
  "sections": [
    {{
      "name": "Section A",
      "questions": [
        {{"id": "question_id_1"}},
        {{"id": "question_id_2"}}
      ]
    }}
  ]
}}

Try to balance unit coverage and avoid repeating the same question.
""",
        ),
    ]
)


async def generate_paper_from_question_bank(template: QuestionPaperTemplate) -> dict:
    """Select bank questions with an LLM and persist a final paper."""
    cursor = question_bank_collection.find({"syllabus_id": template.syllabus_id})
    bank_docs = await cursor.to_list(length=1000)
    if not bank_docs:
        raise ValueError("Question bank is empty for this syllabus. Generate it first.")

    bank_payload = [
        {
            "id": str(d["_id"]),
            "unit": d.get("unit", ""),
            "bloom_level": d.get("bloom_level", ""),
            "marks": d.get("marks", 5),
        }
        for d in bank_docs
    ]

    template_payload = {
        "title": template.title,
        "sections": [
            {
                "name": s.name,
                "bloom_level": s.bloom_level.value,
                "num_questions": s.num_questions,
            }
            for s in template.sections
        ],
    }

    llm = _get_chat_model()
    messages = PAPER_SELECTION_TEMPLATE.format_messages(
        question_bank=json.dumps(bank_payload, indent=2),
        template=json.dumps(template_payload, indent=2),
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
        sections = data.get("sections", [])
    except json.JSONDecodeError as e:
        logger.error("Failed to parse question paper selection JSON: %s", e)
        raise ValueError("LLM returned invalid JSON while selecting questions for paper")

    bank_by_id = {str(d["_id"]): d for d in bank_docs}
    questions: List[PaperQuestion] = []
    q_number = 1
    total_marks = 0

    for sec in sections:
        for q in sec.get("questions", []):
            qid = q.get("id")
            if not qid or qid not in bank_by_id:
                continue
            src = bank_by_id[qid]
            marks = src.get("marks", 5)
            pq = PaperQuestion(
                question_number=q_number,
                question_text=src.get("question", ""),
                sub_questions=[],
                marks=marks,
                bloom_level=src.get("bloom_level", ""),
                topic=src.get("topic", ""),
                model_answer="",
                unit=src.get("unit", ""),
                bank_id=qid,
            )
            questions.append(pq)
            total_marks += marks
            q_number += 1

    paper_doc = {
        "syllabus_id": template.syllabus_id,
        "exam_title": template.title,
        "total_marks": total_marks,
        "duration_minutes": 180,
        "questions": [q.model_dump() for q in questions],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await final_question_paper_collection.insert_one(paper_doc)
    paper_doc["_id"] = result.inserted_id
    logger.info("Generated paper with %d questions and %d total marks", len(questions), total_marks)
    return paper_doc
