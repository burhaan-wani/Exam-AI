import logging
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from bson import ObjectId

from app.database import syllabus_collection, question_bank_collection, documents_collection, final_question_paper_collection
from app.models.schemas import (
    QuestionBankItem,
    QuestionBankCreateRequest,
    QuestionPaperTemplate,
)
from app.services.syllabus_parser import parse_syllabus_units
from app.services.question_bank_generator import generate_question_bank_for_syllabus
from app.services.paper_generator import generate_paper_from_question_bank
from app.utils.file_parser import extract_text

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


@router.post("/upload-reference-material")
async def upload_reference_material(
    syllabus_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload optional reference material (PDF/DOCX/TXT) to be used for RAG."""
    file_bytes = await file.read()
    filename = file.filename or "reference"

    try:
        content = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    doc = {
        "syllabus_id": syllabus_id,
        "file_name": filename,
        "file_type": filename.split(".")[-1].lower() if "." in filename else "txt",
        "content": content,
    }
    result = await documents_collection.insert_one(doc)
    logger.info("Uploaded reference material '%s' for syllabus %s", filename, syllabus_id)

    return {
        "id": str(result.inserted_id),
        "syllabus_id": syllabus_id,
        "file_name": filename,
    }


@router.post("/review-question")
async def review_question_in_paper(
    paper_id: str = Form(...),
    question_number: int = Form(...),
):
    """
    Simple HITL endpoint for the new pipeline:
    replace a question in a generated paper with another from the bank
    matching the same bloom level and unit, avoiding duplicates.
    """
    paper = await final_question_paper_collection.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    questions = paper.get("questions", [])
    target = next((q for q in questions if q.get("question_number") == question_number), None)
    if not target:
        raise HTTPException(404, "Question not found in paper")

    bloom_level = target.get("bloom_level", "")
    unit = target.get("unit", "")
    used_bank_ids = {q.get("bank_id") for q in questions if q.get("bank_id")}

    query: dict = {"syllabus_id": paper.get("syllabus_id", ""), "bloom_level": bloom_level}
    if unit:
        query["unit"] = unit

    cursor = question_bank_collection.find(query)
    candidates = [d async for d in cursor if str(d["_id"]) not in used_bank_ids]
    if not candidates:
        raise HTTPException(400, "No alternative questions available in question bank")

    replacement = candidates[0]
    target.update(
        {
            "question_text": replacement.get("question", ""),
            "topic": replacement.get("topic", ""),
            "marks": replacement.get("marks", 5),
            "bloom_level": replacement.get("bloom_level", bloom_level),
            "unit": replacement.get("unit", unit),
            "bank_id": str(replacement["_id"]),
        }
    )

    await final_question_paper_collection.update_one(
        {"_id": ObjectId(paper_id)},
        {"$set": {"questions": questions}},
    )

    return {"paper_id": paper_id, "question_number": question_number, "status": "replaced"}


@router.get("/final-paper")
async def get_final_paper(paper_id: str):
    """Get a final question paper (alias for legacy paper endpoint)."""
    try:
        doc = await final_question_paper_collection.find_one({"_id": ObjectId(paper_id)})
    except Exception:
        raise HTTPException(400, "Invalid paper ID")

    if not doc:
        raise HTTPException(404, "Question paper not found")

    return {
        "id": str(doc["_id"]),
        "syllabus_id": doc.get("syllabus_id", ""),
        "exam_title": doc.get("exam_title", ""),
        "total_marks": doc.get("total_marks", 0),
        "duration_minutes": doc.get("duration_minutes", 180),
        "questions": doc.get("questions", []),
        "created_at": doc.get("created_at", ""),
    }

