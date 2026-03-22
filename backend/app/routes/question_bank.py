import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.database import (
    syllabus_collection,
    question_bank_collection,
    documents_collection,
    final_question_paper_collection,
    paper_templates_collection,
)
from app.dependencies.auth import require_teacher
from app.models.schemas import (
    FinalPaperFinalizeRequest,
    FinalPaperOut,
    FinalPaperQuestionReplaceRequest,
    FinalPaperQuestionUpdateRequest,
    FinalPaperMetadataUpdateRequest,
    QuestionBankItem,
    QuestionBankCreateRequest,
    QuestionBankUpdateRequest,
    PaperTemplateBlueprint,
    PaperTemplateOut,
    PaperTemplateUpdateRequest,
    QuestionPaperTemplate,
    QuestionReviewStatus,
    TemplatePaperGenerationRequest,
    FinalPaperStatus,
)
from app.services.document_loader import build_langchain_documents, mark_reference_document_indexed, save_reference_document
from app.services.paper_generator import generate_paper_from_question_bank, generate_paper_from_uploaded_template
from app.services.paper_template_parser import parse_paper_template_blueprint, validate_paper_template_blueprint
from app.services.question_bank_generator import (
    _format_question_bank_item,
    generate_question_bank_for_syllabus,
    generate_single_question,
)
from app.services.syllabus_parser import parse_syllabus_units
from app.services.vector_store import upsert_syllabus_documents
from app.utils.file_parser import extract_text, extract_template_source

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


async def _get_latest_template_or_404(syllabus_id: str) -> dict:
    doc = await paper_templates_collection.find_one({"syllabus_id": syllabus_id}, sort=[("uploaded_at", -1)])
    if not doc:
        raise HTTPException(404, "Paper template not found")
    return doc


def _build_template_response(doc: dict) -> PaperTemplateOut:
    raw_blueprint = doc.get("blueprint", {})
    blueprint = raw_blueprint if isinstance(raw_blueprint, PaperTemplateBlueprint) else PaperTemplateBlueprint.model_validate(raw_blueprint)
    validation = validate_paper_template_blueprint(blueprint)
    return PaperTemplateOut(
        id=str(doc["_id"]),
        syllabus_id=doc.get("syllabus_id", ""),
        file_name=doc.get("file_name", ""),
        uploaded_at=doc.get("uploaded_at", ""),
        blueprint=blueprint,
        validation=validation,
    )


def _build_final_paper_response(doc: dict) -> FinalPaperOut:
    return FinalPaperOut(
        id=str(doc["_id"]),
        syllabus_id=doc.get("syllabus_id", ""),
        exam_title=doc.get("exam_title", ""),
        total_marks=doc.get("total_marks", 0),
        duration_minutes=doc.get("duration_minutes", 180),
        questions=doc.get("questions", []),
        status=doc.get("status", FinalPaperStatus.DRAFT.value),
        finalized_at=doc.get("finalized_at"),
        created_at=doc.get("created_at", ""),
    )


def _touch_paper(doc: dict) -> dict:
    updated_at = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = updated_at
    return {"updated_at": updated_at}


def _question_has_internal_or(question: dict) -> bool:
    return bool(question.get("alternative_question_text") or question.get("alternative_sub_questions"))


def _question_bank_ids(question: dict) -> set[str]:
    ids = set(question.get("source_bank_ids", []) or [])
    if question.get("bank_id"):
        ids.add(question["bank_id"])
    for sub in question.get("sub_questions", []) or []:
        if sub.get("bank_id"):
            ids.add(sub["bank_id"])
    for sub in question.get("alternative_sub_questions", []) or []:
        if sub.get("bank_id"):
            ids.add(sub["bank_id"])
    return ids


def _paper_used_bank_ids(questions: list[dict], exclude_number: int | None = None) -> set[str]:
    used_ids: set[str] = set()
    for question in questions:
        if exclude_number is not None and question.get("question_number") == exclude_number:
            continue
        used_ids.update(_question_bank_ids(question))
    return used_ids


def _slot_shape(question: dict, slot: str) -> tuple[str, list[dict]]:
    if slot == "alternative":
        return question.get("alternative_question_text", ""), question.get("alternative_sub_questions", []) or []
    return question.get("question_text", ""), question.get("sub_questions", []) or []


def _apply_slot_content(question: dict, slot: str, text: str, sub_questions: list[dict]) -> None:
    if slot == "alternative":
        question["alternative_question_text"] = text
        question["alternative_sub_questions"] = sub_questions
        return
    question["question_text"] = text
    question["sub_questions"] = sub_questions


async def _replace_question_slot_from_bank(paper: dict, target: dict, slot: str) -> dict:
    if slot not in {"primary", "alternative"}:
        raise HTTPException(400, "slot must be either 'primary' or 'alternative'")

    if slot == "alternative" and not _question_has_internal_or(target):
        raise HTTPException(400, "This question does not have an internal OR option to replace")

    _, old_slot_sub_questions = _slot_shape(target, slot)
    old_slot_ids = set()
    if slot == "primary":
        if target.get("bank_id"):
            old_slot_ids.add(target["bank_id"])
        old_slot_ids.update(sub.get("bank_id") for sub in old_slot_sub_questions if sub.get("bank_id"))
    else:
        old_slot_ids.update(sub.get("bank_id") for sub in old_slot_sub_questions if sub.get("bank_id"))

    current_sub_questions = old_slot_sub_questions
    required_count = max(len(current_sub_questions), 1)
    used_bank_ids = _paper_used_bank_ids(paper.get("questions", []), exclude_number=target.get("question_number"))
    used_bank_ids.update(bank_id for bank_id in old_slot_ids if bank_id)
    unit = target.get("unit", "")
    bloom_level = target.get("bloom_level", "")

    query: dict = {"syllabus_id": paper.get("syllabus_id", "")}
    if unit:
        query["unit"] = unit
    if bloom_level and bloom_level != "Mixed":
        query["bloom_level"] = bloom_level

    cursor = question_bank_collection.find(query)
    candidates = [
        d async for d in cursor
        if str(d["_id"]) not in used_bank_ids and d.get("status", QuestionReviewStatus.PENDING.value) in _CURATED_STATUSES
    ]
    if len(candidates) < required_count:
        raise HTTPException(400, "No suitable replacement questions available while preserving the current paper constraints")

    selected = candidates[:required_count]
    slot_bank_ids = [str(doc["_id"]) for doc in selected]

    if current_sub_questions:
        replacement_sub_questions = []
        for index, sub_question in enumerate(current_sub_questions):
            doc = selected[min(index, len(selected) - 1)]
            replacement_sub_questions.append(
                {
                    "label": sub_question.get("label", ""),
                    "text": doc.get("question", ""),
                    "marks": int(sub_question.get("marks", 0) or 0),
                    "model_answer": doc.get("model_answer", ""),
                    "bank_id": str(doc["_id"]),
                }
            )
        _apply_slot_content(target, slot, "", replacement_sub_questions)
    else:
        doc = selected[0]
        _apply_slot_content(target, slot, doc.get("question", ""), [])
        if slot == "primary":
            target["bank_id"] = str(doc["_id"])

    current_source_ids = set(target.get("source_bank_ids", []) or [])
    current_source_ids.difference_update(old_slot_ids)
    current_source_ids.update(slot_bank_ids)
    target["source_bank_ids"] = list(current_source_ids)

    slot_topics = [doc.get("topic", "") for doc in selected if doc.get("topic")]
    if slot_topics:
        combined_topics = [part.strip() for part in (target.get("topic", "") or "").split(",") if part.strip()]
        combined_topics.extend(slot_topics)
        target["topic"] = ", ".join(dict.fromkeys(combined_topics))

    if slot == "primary":
        representative = selected[0]
        target["bank_id"] = str(representative["_id"])
        target["bloom_level"] = representative.get("bloom_level", target.get("bloom_level", ""))
        target["unit"] = representative.get("unit", target.get("unit", ""))
        if not current_sub_questions:
            target["marks"] = int(representative.get("marks", 0) or 0) or _fallback_marks_for_bloom(
                representative.get("bloom_level", target.get("bloom_level", ""))
            )

    return target


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

    return _build_final_paper_response(paper_doc)


@router.post("/upload-paper-template", response_model=PaperTemplateOut)
async def upload_paper_template(
    syllabus_id: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(require_teacher),
):
    """Upload one or more previous paper template files and extract a combined structural blueprint."""
    syllabus = await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    if not files:
        raise HTTPException(400, "Upload at least one template file.")

    raw_text_parts: list[str] = []
    page_images: list[str] = []
    uploaded_names: list[str] = []

    try:
        for file in files:
            file_bytes = await file.read()
            filename = file.filename or "paper-template"
            uploaded_names.append(filename)
            extracted_text, extracted_images = extract_template_source(file_bytes, filename)
            if extracted_text.strip():
                raw_text_parts.append(extracted_text.strip())
            page_images.extend(extracted_images)

        raw_text = "\n\n".join(raw_text_parts)
        unit_names = [topic.get("unit", "") for topic in syllabus.get("topics", []) if topic.get("unit")]
        blueprint = await parse_paper_template_blueprint(raw_text, unit_names, page_images=page_images)
    except ValueError as e:
        raise HTTPException(400, str(e))

    uploaded_at = datetime.now(timezone.utc).isoformat()
    await paper_templates_collection.delete_many({"syllabus_id": syllabus_id})
    combined_name = uploaded_names[0] if len(uploaded_names) == 1 else f"{uploaded_names[0]} (+{len(uploaded_names) - 1} more)"
    doc = {
        "syllabus_id": syllabus_id,
        "file_name": combined_name,
        "raw_text": raw_text,
        "blueprint": blueprint.model_dump(),
        "uploaded_at": uploaded_at,
    }
    result = await paper_templates_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _build_template_response(doc)


@router.get("/paper-template", response_model=PaperTemplateOut)
async def get_paper_template(
    syllabus_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Get the latest uploaded paper template for a syllabus."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    doc = await _get_latest_template_or_404(syllabus_id)
    return _build_template_response(doc)


@router.patch("/paper-template", response_model=PaperTemplateOut)
async def update_paper_template(
    syllabus_id: str,
    body: PaperTemplateUpdateRequest,
    current_user: dict = Depends(require_teacher),
):
    """Save a teacher-reviewed blueprint for the latest uploaded paper template."""
    await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    doc = await _get_latest_template_or_404(syllabus_id)
    updated_blueprint = body.blueprint
    validation = validate_paper_template_blueprint(updated_blueprint)
    updated_at = datetime.now(timezone.utc).isoformat()

    await paper_templates_collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"blueprint": updated_blueprint.model_dump(), "reviewed_at": updated_at}},
    )
    doc["blueprint"] = updated_blueprint
    doc["reviewed_at"] = updated_at
    return PaperTemplateOut(
        id=str(doc["_id"]),
        syllabus_id=doc.get("syllabus_id", ""),
        file_name=doc.get("file_name", ""),
        uploaded_at=doc.get("uploaded_at", ""),
        blueprint=updated_blueprint,
        validation=validation,
    )


@router.post("/generate-question-paper-from-template")
async def generate_question_paper_from_template(
    body: TemplatePaperGenerationRequest,
    current_user: dict = Depends(require_teacher),
):
    """Generate a paper from curated bank questions using the uploaded paper template blueprint."""
    await _get_owned_syllabus_or_404(body.syllabus_id, current_user["id"])
    template_doc = await _get_latest_template_or_404(body.syllabus_id)
    blueprint = PaperTemplateBlueprint.model_validate(template_doc.get("blueprint", {}))
    validation = validate_paper_template_blueprint(blueprint)
    if not validation.is_valid:
        raise HTTPException(400, "Review and fix the template blueprint before generating the final paper.")
    try:
        paper_doc = await generate_paper_from_uploaded_template(body.syllabus_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return _build_final_paper_response(paper_doc)


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
    """Backward-compatible alias for replacing the primary slot of a paper question."""
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])

    questions = paper.get("questions", [])
    target = next((q for q in questions if q.get("question_number") == question_number), None)
    if not target:
        raise HTTPException(404, "Question not found in paper")

    await _replace_question_slot_from_bank(paper, target, "primary")

    await final_question_paper_collection.update_one(
        {"_id": ObjectId(paper_id)},
        {"$set": {"questions": questions, **_touch_paper(paper), "status": FinalPaperStatus.DRAFT.value, "finalized_at": None}},
    )

    return {"paper_id": paper_id, "question_number": question_number, "status": "replaced"}


@router.get("/final-paper", response_model=FinalPaperOut)
async def get_final_paper(
    paper_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Alias for fetching a generated paper."""
    doc = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    return _build_final_paper_response(doc)


@router.patch("/final-paper/{paper_id}", response_model=FinalPaperOut)
async def update_final_paper_metadata(
    paper_id: str,
    body: FinalPaperMetadataUpdateRequest,
    current_user: dict = Depends(require_teacher),
):
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    updates: dict = {}

    if body.exam_title is not None:
        cleaned = body.exam_title.strip()
        if not cleaned:
            raise HTTPException(400, "Exam title cannot be empty")
        updates["exam_title"] = cleaned
    if body.total_marks is not None:
        if body.total_marks <= 0:
            raise HTTPException(400, "Total marks must be greater than zero")
        updates["total_marks"] = body.total_marks
    if body.duration_minutes is not None:
        if body.duration_minutes <= 0:
            raise HTTPException(400, "Duration must be greater than zero")
        updates["duration_minutes"] = body.duration_minutes

    if not updates:
        return _build_final_paper_response(paper)

    updates.update(_touch_paper(paper))
    updates["status"] = FinalPaperStatus.DRAFT.value
    updates["finalized_at"] = None
    await final_question_paper_collection.update_one({"_id": paper["_id"]}, {"$set": updates})
    paper.update(updates)
    return _build_final_paper_response(paper)


@router.patch("/final-paper/{paper_id}/questions/{question_number}", response_model=FinalPaperOut)
async def update_final_paper_question(
    paper_id: str,
    question_number: int,
    body: FinalPaperQuestionUpdateRequest,
    current_user: dict = Depends(require_teacher),
):
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    questions = paper.get("questions", [])
    target = next((q for q in questions if q.get("question_number") == question_number), None)
    if not target:
        raise HTTPException(404, "Question not found in paper")

    if body.question_text is not None:
        target["question_text"] = body.question_text.strip()
    if body.sub_questions is not None:
        target["sub_questions"] = [sub.model_dump() for sub in body.sub_questions]
    if body.alternative_question_text is not None:
        target["alternative_question_text"] = body.alternative_question_text.strip()
    if body.alternative_sub_questions is not None:
        target["alternative_sub_questions"] = [sub.model_dump() for sub in body.alternative_sub_questions]
    if body.marks is not None:
        if body.marks <= 0:
            raise HTTPException(400, "Question marks must be greater than zero")
        target["marks"] = body.marks
    if body.bloom_level is not None:
        target["bloom_level"] = body.bloom_level.strip()
    if body.topic is not None:
        target["topic"] = body.topic.strip()
    if body.unit is not None:
        target["unit"] = body.unit.strip()
    if body.or_with_next is not None:
        target["or_with_next"] = body.or_with_next

    if target.get("sub_questions") and target.get("question_text"):
        raise HTTPException(400, "Use either question text or sub-questions for the primary slot, not both")
    if target.get("alternative_sub_questions") and target.get("alternative_question_text"):
        raise HTTPException(400, "Use either alternative question text or alternative sub-questions, not both")

    await final_question_paper_collection.update_one(
        {"_id": paper["_id"]},
        {"$set": {"questions": questions, **_touch_paper(paper), "status": FinalPaperStatus.DRAFT.value, "finalized_at": None}},
    )
    paper["questions"] = questions
    paper["status"] = FinalPaperStatus.DRAFT.value
    paper["finalized_at"] = None
    return _build_final_paper_response(paper)


@router.post("/final-paper/{paper_id}/questions/{question_number}/replace", response_model=FinalPaperOut)
async def replace_final_paper_question(
    paper_id: str,
    question_number: int,
    body: FinalPaperQuestionReplaceRequest,
    current_user: dict = Depends(require_teacher),
):
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    questions = paper.get("questions", [])
    target = next((q for q in questions if q.get("question_number") == question_number), None)
    if not target:
        raise HTTPException(404, "Question not found in paper")

    await _replace_question_slot_from_bank(paper, target, body.slot)
    await final_question_paper_collection.update_one(
        {"_id": paper["_id"]},
        {"$set": {"questions": questions, **_touch_paper(paper), "status": FinalPaperStatus.DRAFT.value, "finalized_at": None}},
    )
    paper["questions"] = questions
    paper["status"] = FinalPaperStatus.DRAFT.value
    paper["finalized_at"] = None
    return _build_final_paper_response(paper)


@router.post("/final-paper/{paper_id}/finalize", response_model=FinalPaperOut)
async def finalize_final_paper(
    paper_id: str,
    body: FinalPaperFinalizeRequest,
    current_user: dict = Depends(require_teacher),
):
    paper = await _get_teacher_paper_or_404(paper_id, current_user["id"])
    status_value = body.status.value
    updates = _touch_paper(paper)
    updates["status"] = status_value
    updates["finalized_at"] = datetime.now(timezone.utc).isoformat() if status_value == FinalPaperStatus.FINALIZED.value else None

    await final_question_paper_collection.update_one({"_id": paper["_id"]}, {"$set": updates})
    paper.update(updates)
    return _build_final_paper_response(paper)
