import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.database import syllabus_collection, question_bank_collection, documents_collection, final_question_paper_collection
from app.dependencies.auth import require_teacher
from app.models.schemas import (
    QuestionBankItem,
    QuestionBankCreateRequest,
    QuestionBankUpdateRequest,
    QuestionPaperTemplate,
    QuestionReviewStatus,
)
from app.services.document_loader import build_langchain_documents, mark_reference_document_indexed, save_reference_document
from app.services.paper_generator import generate_paper_from_question_bank
from app.services.question_bank_generator import (
    _format_question_bank_item,
    generate_question_bank_for_syllabus,
    generate_single_question,
)
from app.services.syllabus_parser import parse_syllabus_units
from app.services.vector_store import upsert_syllabus_documents
from app.utils.file_parser import extract_text

logger = logging.getLogger(__name__)
router = APIRouter()
_CURATED_STATUSES = {QuestionReviewStatus.APPROVED.value, QuestionReviewStatus.EDITED.value}


def _fallback_marks_for_bloom(bloom_level: str) -> int:
    return {
        "Remember": 2,
        "Apply": 5,
        "Analyze": 10,
    }.get(bloom_level, 5)


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


async def _get_teacher_question_or_404(question_id: str, teacher_id: str) -> dict:
    try:
        doc = await question_bank_collection.find_one({"_id": ObjectId(question_id)})
    except Exception:
        raise HTTPException(400, "Invalid question ID")

    if not doc:
        raise HTTPException(404, "Question not found")

    await _get_owned_syllabus_or_404(doc.get("syllabus_id", ""), teacher_id)
    return doc


@router.post("/upload-syllabus")
async def upload_syllabus_new(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_teacher),
):
    """Upload a syllabus for the new question-bank teacher pipeline."""
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    try:
        raw_text, parsed_units = await parse_syllabus_units(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    created_at = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": current_user["id"],
        "filename": filename,
        "raw_text": raw_text,
        "topics": parsed_units,
        "created_at": created_at,
    }
    result = await syllabus_collection.insert_one(doc)
    units = [unit.get("unit", "") for unit in parsed_units]
    logger.info("Syllabus uploaded: %s (%d units) by %s", filename, len(units), current_user["email"])

    return {
        "id": str(result.inserted_id),
        "filename": filename,
        "units": units,
        "topics": parsed_units,
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
    status: str | None = None,
    current_user: dict = Depends(require_teacher),
):
    """List question bank entries for a teacher-owned syllabus."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])

    query: dict = {"syllabus_id": syllabus_id}
    if unit:
        query["unit"] = unit
    if bloom_level:
        query["bloom_level"] = bloom_level
    if status:
        query["status"] = status

    cursor = question_bank_collection.find(query)
    docs = await cursor.to_list(length=500)
    return [_format_question_bank_item(d) for d in docs]


@router.patch("/question-bank/{question_id}", response_model=QuestionBankItem)
async def update_question_bank_item(
    question_id: str,
    body: QuestionBankUpdateRequest,
    current_user: dict = Depends(require_teacher),
):
    """Approve, reject, or edit a generated bank question."""
    doc = await _get_teacher_question_or_404(question_id, current_user["id"])

    updates: dict = {}
    if body.question is not None:
        cleaned = body.question.strip()
        if not cleaned:
            raise HTTPException(400, "Question text cannot be empty")
        updates["question"] = cleaned
        updates["status"] = QuestionReviewStatus.EDITED.value

    if body.status is not None:
        updates["status"] = body.status.value

    if not updates:
        return _format_question_bank_item(doc)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await question_bank_collection.update_one({"_id": doc["_id"]}, {"$set": updates})
    doc.update(updates)
    return _format_question_bank_item(doc)


@router.post("/question-bank/{question_id}/regenerate", response_model=QuestionBankItem)
async def regenerate_question_bank_item(
    question_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Regenerate a single bank question for the same unit, topic, and Bloom level."""
    doc = await _get_teacher_question_or_404(question_id, current_user["id"])
    bloom_level = doc.get("bloom_level", "Remember")
    bloom_level_int = {
        "Remember": 1,
        "Apply": 2,
        "Analyze": 3,
    }.get(bloom_level, 1)

    try:
        regenerated = await generate_single_question(
            syllabus_id=doc.get("syllabus_id", ""),
            unit_name=doc.get("unit", ""),
            topic_name=doc.get("topic", ""),
            bloom_level=bloom_level_int,
            previous_question=doc.get("question", ""),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    regenerated["updated_at"] = datetime.now(timezone.utc).isoformat()
    regenerated["marks"] = 0
    await question_bank_collection.update_one({"_id": doc["_id"]}, {"$set": regenerated})
    doc.update(regenerated)
    return _format_question_bank_item(doc)


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
    """Upload optional reference material and index it into the persistent syllabus retriever."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    file_bytes = await file.read()
    filename = file.filename or "reference"
    file_type = filename.split(".")[-1].lower() if "." in filename else "txt"

    try:
        content = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    stored = await save_reference_document(
        syllabus_id=syllabus_id,
        file_name=filename,
        file_type=file_type,
        content=content,
    )
    document_id = str(stored["_id"])
    lc_documents = build_langchain_documents(
        syllabus_id=syllabus_id,
        file_name=filename,
        file_type=file_type,
        content=content,
        document_id=document_id,
    )
    chunk_count = upsert_syllabus_documents(syllabus_id, document_id, lc_documents)
    await mark_reference_document_indexed(stored["_id"], chunk_count)
    logger.info("Uploaded and indexed reference material '%s' for syllabus %s", filename, syllabus_id)

    return {
        "id": document_id,
        "syllabus_id": syllabus_id,
        "file_name": filename,
        "uploaded_at": stored.get("uploaded_at", ""),
        "chunk_count": chunk_count,
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
            "indexed_at": d.get("indexed_at"),
            "chunk_count": d.get("chunk_count", 0),
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
    candidates = [
        d async for d in cursor
        if str(d["_id"]) not in used_bank_ids and d.get("status", QuestionReviewStatus.PENDING.value) in _CURATED_STATUSES
    ]
    if not candidates:
        raise HTTPException(400, "No alternative questions available in question bank")

    replacement = candidates[0]
    target.update(
        {
            "question_text": replacement.get("question", ""),
            "topic": replacement.get("topic", ""),
            "marks": int(replacement.get("marks", 0) or 0) or _fallback_marks_for_bloom(
                replacement.get("bloom_level", bloom_level)
            ),
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
