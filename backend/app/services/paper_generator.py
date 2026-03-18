import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.database import question_bank_collection, final_question_paper_collection, paper_templates_collection, syllabus_collection
from app.models.schemas import PaperQuestion, QuestionPaperTemplate, QuestionReviewStatus

logger = logging.getLogger(__name__)
settings = get_settings()
_DEFAULT_MARKS_BY_BLOOM = {
    "Remember": 2,
    "Apply": 5,
    "Analyze": 10,
}
_CURATED_STATUSES = {QuestionReviewStatus.APPROVED.value, QuestionReviewStatus.EDITED.value}


def _get_chat_model() -> ChatOpenAI:
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    return ChatOpenAI(model=settings.openrouter_model, temperature=0.2)


def _resolve_question_marks(doc: dict) -> int:
    stored_marks = int(doc.get("marks", 0) or 0)
    if stored_marks > 0:
        return stored_marks
    return _DEFAULT_MARKS_BY_BLOOM.get(doc.get("bloom_level", ""), 5)


def _extract_unit_key(unit_label: str) -> str:
    match = re.search(r"(unit|module|chapter|part)\s+(\d+)", (unit_label or "").lower())
    if not match:
        return (unit_label or "").strip().lower()
    return f"{match.group(1)} {match.group(2)}"


def _ordered_syllabus_units(syllabus_topics: list[dict]) -> list[str]:
    units = [topic.get("unit", "") for topic in syllabus_topics if topic.get("unit")]
    return sorted(
        units,
        key=lambda unit: tuple(int(num) for num in re.findall(r"\d+", unit)) or (999,),
    )


def _resolve_group_unit_hint(group: dict, group_index: int, total_groups: int, ordered_units: list[str]) -> str:
    if ordered_units and total_groups >= len(ordered_units) and total_groups % len(ordered_units) == 0:
        groups_per_unit = max(total_groups // len(ordered_units), 1)
        unit_index = min((group_index - 1) // groups_per_unit, len(ordered_units) - 1)
        return ordered_units[unit_index]

    if ordered_units and total_groups == len(ordered_units):
        return ordered_units[min(group_index - 1, len(ordered_units) - 1)]

    explicit_hint = str(group.get("unit_hint", "") or "").strip()
    if explicit_hint:
        explicit_key = _extract_unit_key(explicit_hint)
        for unit in ordered_units:
            if _extract_unit_key(unit) == explicit_key:
                return unit
        return explicit_hint

    if not ordered_units:
        return explicit_hint

    return ordered_units[(group_index - 1) % len(ordered_units)]


def _select_bank_docs(bank_docs: list[dict], used_ids: set[str], unit_hint: str, count: int) -> list[dict]:
    unit_key = _extract_unit_key(unit_hint)
    candidates = [
        doc for doc in bank_docs
        if str(doc["_id"]) not in used_ids and (not unit_key or _extract_unit_key(doc.get("unit", "")) == unit_key)
    ]
    if len(candidates) < count:
        raise ValueError(f"Not enough curated questions available for {unit_hint or 'the requested template slot'}.")
    return candidates[:count]


def _format_slot_option(selected_docs: list[dict], subparts: list[dict]) -> str:
    if not subparts:
        return selected_docs[0].get("question", "")

    lines: list[str] = []
    for index, subpart in enumerate(subparts):
        doc = selected_docs[min(index, len(selected_docs) - 1)]
        label = (subpart.get("label") or "").strip()
        marks = int(subpart.get("marks", 0) or 0)
        prefix = f"{label}) " if label else ""
        line = f"{prefix}{doc.get('question', '')}"
        if marks > 0:
            line = f"{line} ({marks} marks)"
        lines.append(line)
    return "\n".join(lines)


def _derive_slot_bloom_level(selected_docs: list[dict]) -> str:
    levels = {doc.get("bloom_level", "") for doc in selected_docs if doc.get("bloom_level")}
    if len(levels) == 1:
        return levels.pop()
    return "Mixed"


async def generate_paper_from_uploaded_template(syllabus_id: str) -> dict:
    template_doc = await paper_templates_collection.find_one(
        {"syllabus_id": syllabus_id},
        sort=[("uploaded_at", -1)],
    )
    if not template_doc:
        raise ValueError("Upload a paper template before generating the final paper.")

    cursor = question_bank_collection.find(
        {"syllabus_id": syllabus_id, "status": {"$in": list(_CURATED_STATUSES)}}
    )
    bank_docs = await cursor.to_list(length=1000)
    if not bank_docs:
        raise ValueError("No approved question bank entries found. Review and approve questions first.")

    blueprint = template_doc.get("blueprint", {})
    question_groups = blueprint.get("question_groups", [])
    if not question_groups:
        raise ValueError("The uploaded paper template does not contain any usable question groups.")

    syllabus_doc = None
    try:
        syllabus_doc = await syllabus_collection.find_one({"_id": ObjectId(syllabus_id)})
    except Exception:
        syllabus_doc = None
    ordered_units = _ordered_syllabus_units((syllabus_doc or {}).get("topics", []))

    used_ids: set[str] = set()
    questions: List[PaperQuestion] = []
    total_marks = int(blueprint.get("total_marks", 0) or 0)
    duration_minutes = int(blueprint.get("duration_minutes", 180) or 180)

    for group_index, group in enumerate(question_groups, start=1):
        group_unit_hint = _resolve_group_unit_hint(group, group_index, len(question_groups), ordered_units)
        primary = group.get("primary", {}) or {}
        alternative = group.get("alternative")
        subparts = primary.get("subparts", []) or [{"label": "", "marks": int(group.get("marks", 20) or 20)}]
        primary_docs = _select_bank_docs(bank_docs, used_ids, group_unit_hint, len(subparts))
        for doc in primary_docs:
            used_ids.add(str(doc["_id"]))

        question_text = _format_slot_option(primary_docs, subparts)
        all_docs = list(primary_docs)

        if alternative:
            alternative_subparts = alternative.get("subparts", []) or [{"label": "", "marks": int(group.get("marks", 20) or 20)}]
            alternative_docs = _select_bank_docs(
                bank_docs,
                used_ids,
                group_unit_hint,
                len(alternative_subparts),
            )
            for doc in alternative_docs:
                used_ids.add(str(doc["_id"]))
            question_text = f"{question_text}\n\n(OR)\n\n{_format_slot_option(alternative_docs, alternative_subparts)}"
            all_docs.extend(alternative_docs)

        question_number = int(group.get("question_number", len(questions) + 1))
        unit_hint = group_unit_hint or primary_docs[0].get("unit", "")
        topics = ", ".join(dict.fromkeys(doc.get("topic", "") for doc in all_docs if doc.get("topic")))

        questions.append(
            PaperQuestion(
                question_number=question_number,
                question_text=question_text,
                sub_questions=[],
                marks=int(group.get("marks", 20) or 20),
                bloom_level=_derive_slot_bloom_level(all_docs),
                topic=topics,
                model_answer="",
                unit=unit_hint,
                bank_id=str(primary_docs[0]["_id"]),
                or_with_next=bool(group.get("or_with_next", False)),
            )
        )

    if total_marks <= 0:
        total_marks = sum(question.marks for question in questions)

    paper_doc = {
        "syllabus_id": syllabus_id,
        "exam_title": blueprint.get("title") or template_doc.get("file_name", "Examination"),
        "total_marks": total_marks,
        "duration_minutes": duration_minutes,
        "questions": [q.model_dump() for q in questions],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "template_id": str(template_doc["_id"]),
    }

    result = await final_question_paper_collection.insert_one(paper_doc)
    paper_doc["_id"] = result.inserted_id
    logger.info("Generated template-guided paper with %d questions", len(questions))
    return paper_doc


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
    cursor = question_bank_collection.find(
        {"syllabus_id": template.syllabus_id, "status": {"$in": list(_CURATED_STATUSES)}}
    )
    bank_docs = await cursor.to_list(length=1000)
    if not bank_docs:
        raise ValueError("No approved question bank entries found. Review and approve questions first.")

    bank_payload = [
        {
            "id": str(d["_id"]),
            "unit": d.get("unit", ""),
            "bloom_level": d.get("bloom_level", ""),
            "marks": _resolve_question_marks(d),
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
            marks = _resolve_question_marks(src)
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
