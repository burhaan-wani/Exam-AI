import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.database import syllabus_collection, question_bank_collection, documents_collection, final_question_paper_collection
from app.dependencies.auth import require_teacher
from app.models.schemas import QuestionBankItem, QuestionBankCreateRequest, QuestionPaperTemplate
from app.services.paper_generator import generate_paper_from_question_bank
from app.services.question_bank_generator import generate_question_bank_for_syllabus
from app.services.syllabus_parser import parse_syllabus_units
from app.utils.file_parser import extract_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_owned_syllabus_or_404(syllabus_id: str, teacher_id: str) -> dict:
    try:
        query = {"_id": ObjectId(syllabus_id), "user_id": teacher_id}
    except Exception:
        raise HTTPException(400, "Invalid syllabus ID")

    doc = await syllabus_collection.find_one(query)
    if not doc:
        raise HTTPException(404, "Syllabus not found")
    return doc


async def _get_teacher_paper_or_404(paper_id: str, teacher_id: str) -> dict:
    try:
        paper = await final_question_paper_collection.find_one({"_id": ObjectId(paper_id)})
    except Exception:
        raise HTTPException(400, "Invalid paper ID")

    if not paper:
        raise HTTPException(404, "Paper not found")

    syllabus_id = paper.get("syllabus_id", "")
    await _get_owned_syllabus_or_404(syllabus_id, teacher_id)
    return paper


@router.post("/upload-syllabus")
async def upload_syllabus_new(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_teacher),
):
    """Upload a syllabus for the new question-bank teacher pipeline."""
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    try:
        raw_text, units = await parse_syllabus_units(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    created_at = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": current_user["id"],
        "filename": filename,
        "raw_text": raw_text,
        "topics": [{"name": unit, "unit": unit, "subtopics": []} for unit in units],
        "created_at": created_at,
    }
    result = await syllabus_collection.insert_one(doc)
    logger.info("Syllabus uploaded: %s (%d units) by %s", filename, len(units), current_user["email"])

    return {
        "id": str(result.inserted_id),
        "filename": filename,
        "units": units,
        "unit_count": len(units),
        "created_at": created_at,
    }


@router.post("/generate-question-bank", response_model=list[QuestionBankItem])
async def generate_question_bank(
    body: QuestionBankCreateRequest,
    current_user: dict = Depends(require_teacher),
):
    """Generate and persist a question bank for the given syllabus."""
    await _get_owned_syllabus_or_404(body.syllabus_id, current_user["id"])
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
    current_user: dict = Depends(require_teacher),
):
    """List question bank entries for a teacher-owned syllabus."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])

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
async def generate_question_paper(
    template: QuestionPaperTemplate,
    current_user: dict = Depends(require_teacher),
):
    """Generate a question paper by selecting from the question bank using an LLM."""
    await _get_owned_syllabus_or_404(template.syllabus_id, current_user["id"])
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
    current_user: dict = Depends(require_teacher),
):
    """Upload optional reference material (PDF/DOCX/TXT) to be used for RAG."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    file_bytes = await file.read()
    filename = file.filename or "reference"

    try:
        content = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    uploaded_at = datetime.now(timezone.utc).isoformat()
    doc = {
        "syllabus_id": syllabus_id,
        "file_name": filename,
        "file_type": filename.split(".")[-1].lower() if "." in filename else "txt",
        "content": content,
        "uploaded_at": uploaded_at,
    }
    result = await documents_collection.insert_one(doc)
    logger.info("Uploaded reference material '%s' for syllabus %s", filename, syllabus_id)

    return {
        "id": str(result.inserted_id),
        "syllabus_id": syllabus_id,
        "file_name": filename,
        "uploaded_at": uploaded_at,
    }


@router.get("/reference-material")
async def list_reference_material(
    syllabus_id: str,
    current_user: dict = Depends(require_teacher),
):
    """List reference materials uploaded for a syllabus."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    cursor = documents_collection.find({"syllabus_id": syllabus_id})
    docs = await cursor.to_list(length=200)
    return [
        {
            "id": str(d["_id"]),
            "syllabus_id": d.get("syllabus_id", ""),
            "file_name": d.get("file_name", ""),
            "file_type": d.get("file_type", ""),
            "uploaded_at": d.get("uploaded_at", ""),
        }
        for d in docs
    ]


@router.post("/review-question")
async def review_question_in_paper(
    paper_id: str = Form(...),
    question_number: int = Form(...),
    current_user: dict = Depends(require_teacher),
):
    """Replace a paper question with another bank question from the same unit and Bloom level."""
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])

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
async def get_final_paper(
    paper_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Alias for fetching a generated paper."""
    doc = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    return {
        "id": str(doc["_id"]),
        "syllabus_id": doc.get("syllabus_id", ""),
        "exam_title": doc.get("exam_title", ""),
        "total_marks": doc.get("total_marks", 0),
        "duration_minutes": doc.get("duration_minutes", 180),
        "questions": doc.get("questions", []),
        "created_at": doc.get("created_at", ""),
    }
