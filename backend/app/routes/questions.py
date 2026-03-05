import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import question_blueprint_collection, generated_questions_collection
from app.models.schemas import BlueprintCreate, QuestionGenerateRequest
from app.services.mark_allocator import allocate_marks
from app.services.question_generator import generate_questions_for_blueprint, format_question_out

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/blueprint")
async def create_blueprint(body: BlueprintCreate):
    """Create a question blueprint with Bloom configurations and mark allocation."""
    # Run mark allocation
    configs_dicts = [c.model_dump() for c in body.configs]
    allocated = allocate_marks(body.total_marks, configs_dicts)

    doc = {
        "syllabus_id": body.syllabus_id,
        "exam_title": body.exam_title,
        "total_marks": body.total_marks,
        "duration_minutes": body.duration_minutes,
        "configs": allocated,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await question_blueprint_collection.insert_one(doc)
    logger.info(f"Blueprint created: {result.inserted_id}")

    return {
        "id": str(result.inserted_id),
        "syllabus_id": body.syllabus_id,
        "exam_title": body.exam_title,
        "total_marks": body.total_marks,
        "duration_minutes": body.duration_minutes,
        "configs": allocated,
        "created_at": doc["created_at"],
    }


@router.get("/blueprint/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    """Get a blueprint by ID."""
    doc = await question_blueprint_collection.find_one({"_id": ObjectId(blueprint_id)})
    if not doc:
        raise HTTPException(404, "Blueprint not found")
    return {
        "id": str(doc["_id"]),
        "syllabus_id": doc.get("syllabus_id", ""),
        "exam_title": doc.get("exam_title", ""),
        "total_marks": doc.get("total_marks", 0),
        "duration_minutes": doc.get("duration_minutes", 180),
        "configs": doc.get("configs", []),
        "created_at": doc.get("created_at", ""),
    }


@router.post("/generate")
async def generate_questions(body: QuestionGenerateRequest):
    """Generate questions for a blueprint using LLM."""
    try:
        questions = await generate_questions_for_blueprint(body.blueprint_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        raise HTTPException(500, f"Question generation failed: {str(e)}")

    return {
        "count": len(questions),
        "questions": [format_question_out(q) for q in questions],
    }


@router.get("/by-blueprint/{blueprint_id}")
async def list_questions_by_blueprint(blueprint_id: str):
    """List all generated questions for a blueprint."""
    cursor = generated_questions_collection.find({"blueprint_id": blueprint_id})
    docs = await cursor.to_list(length=200)
    return [format_question_out(d) for d in docs]
