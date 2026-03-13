from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import final_question_paper_collection
from app.dependencies.auth import require_student

router = APIRouter()


@router.get("/{paper_id}")
async def get_paper(paper_id: str, _current_user: dict = Depends(require_student)):
    """Get a generated question paper for the student submission flow."""
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
