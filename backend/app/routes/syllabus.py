from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import final_question_paper_collection, syllabus_collection
from app.dependencies.auth import require_teacher

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


@router.get("/list")
async def list_syllabi(current_user: dict = Depends(require_teacher)):
    """List the current teacher's syllabi."""
    cursor = syllabus_collection.find({"user_id": current_user["id"]})
    docs = await cursor.to_list(length=100)
    items = []
    for d in docs:
        syllabus_id = str(d["_id"])
        latest_paper = await final_question_paper_collection.find_one(
            {"syllabus_id": syllabus_id},
            sort=[("created_at", -1)],
        )
        items.append(
            {
                "id": syllabus_id,
                "filename": d.get("filename", ""),
                "topic_count": len(d.get("topics", [])),
                "created_at": d.get("created_at", ""),
                "latest_final_paper_id": str(latest_paper["_id"]) if latest_paper else None,
                "latest_final_paper_status": latest_paper.get("status") if latest_paper else None,
                "latest_finalized_at": latest_paper.get("finalized_at") if latest_paper else None,
            }
        )
    return items


@router.get("/{syllabus_id}")
async def get_syllabus(syllabus_id: str, current_user: dict = Depends(require_teacher)):
    """Get syllabus details for the current teacher."""
    doc = await _get_owned_syllabus_or_404(syllabus_id, current_user["id"])
    latest_paper = await final_question_paper_collection.find_one(
        {"syllabus_id": syllabus_id},
        sort=[("created_at", -1)],
    )
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id", ""),
        "filename": doc.get("filename", ""),
        "raw_text": doc.get("raw_text", ""),
        "topics": doc.get("topics", []),
        "created_at": doc.get("created_at", ""),
        "latest_final_paper_id": str(latest_paper["_id"]) if latest_paper else None,
        "latest_final_paper_status": latest_paper.get("status") if latest_paper else None,
        "latest_finalized_at": latest_paper.get("finalized_at") if latest_paper else None,
    }
