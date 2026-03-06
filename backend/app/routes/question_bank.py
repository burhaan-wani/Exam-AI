import logging
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from bson import ObjectId

from app.database import syllabus_collection, question_bank_collection
from app.models.schemas import (
    QuestionBankItem,
    QuestionBankCreateRequest,
    QuestionBankListQuery,
    QuestionPaperTemplate,
)
from app.services.syllabus_parser import parse_syllabus_units
from app.services.question_bank_generator import generate_question_bank_for_syllabus
from app.services.paper_generator import generate_paper_from_question_bank

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-syllabus")
async def upload_syllabus_new(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous"),
):
    """
    New syllabus upload endpoint for the two-stage pipeline.
    Reuses the existing topic extraction logic and stores the syllabus document.
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    try:
        raw_text, units = await parse_syllabus_units(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    doc = {
        "user_id": user_id,
        "filename": filename,
        "raw_text": raw_text,
        "topics": [{"name": u, "unit": u, "subtopics": []} for u in units],
    }
    result = await syllabus_collection.insert_one(doc)
    logger.info("Syllabus (new pipeline) uploaded: %s, %d units", filename, len(units))

    return {
        "id": str(result.inserted_id),
        "filename": filename,
        "units": units,
        "unit_count": len(units),
    }


@router.post("/generate-question-bank", response_model=list[QuestionBankItem])
async def generate_question_bank(body: QuestionBankCreateRequest):
    """Generate and persist a question bank for the given syllabus."""
    try:
        items = await generate_question_bank_for_syllabus(body.syllabus_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return items


@router.get("/question-bank", response_model=list[QuestionBankItem])
async def list_question_bank(
    syllabus_id: str,
    unit: str | None = None,
    bloom_level: str | None = None,
):
    """List question bank entries for a syllabus, optionally filtered."""
    query: dict = {"syllabus_id": syllabus_id}
    if unit:
        query["unit"] = unit
    if bloom_level:
        query["bloom_level"] = bloom_level

    cursor = question_bank_collection.find(query)
    docs = await cursor.to_list(length=500)
    return [
        QuestionBankItem(
            id=str(d["_id"]),
            question=d.get("question", ""),
            unit=d.get("unit", ""),
            topic=d.get("topic", ""),
            bloom_level=d.get("bloom_level", "Remember"),
            marks=d.get("marks", 5),
            difficulty=d.get("difficulty", "medium"),
            source_context=d.get("source_context"),
            created_at=d.get("created_at", ""),
        )
        for d in docs
    ]


@router.post("/generate-question-paper")
async def generate_question_paper(template: QuestionPaperTemplate):
    """Generate a question paper by selecting from the question bank using an LLM."""
    try:
        paper_doc = await generate_paper_from_question_bank(template)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "id": str(paper_doc["_id"]),
        "syllabus_id": paper_doc.get("syllabus_id", ""),
        "exam_title": paper_doc.get("exam_title", ""),
        "total_marks": paper_doc.get("total_marks", 0),
        "duration_minutes": paper_doc.get("duration_minutes", 180),
        "questions": paper_doc.get("questions", []),
        "created_at": paper_doc.get("created_at", ""),
    }

