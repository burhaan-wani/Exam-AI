from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import syllabus_collection

router = APIRouter()


@router.get("/list")
async def list_syllabi(user_id: str = "anonymous"):
    """List all uploaded syllabi for a user."""
    cursor = syllabus_collection.find({"user_id": user_id})
    docs = await cursor.to_list(length=100)
    return [
        {
            "id": str(d["_id"]),
            "filename": d.get("filename", ""),
            "topic_count": len(d.get("topics", [])),
            "created_at": d.get("created_at", ""),
        }
        for d in docs
    ]


@router.get("/{syllabus_id}")
async def get_syllabus(syllabus_id: str):
    """Get syllabus details used by the new teacher pipeline."""
    doc = await syllabus_collection.find_one({"_id": ObjectId(syllabus_id)})
    if not doc:
        raise HTTPException(404, "Syllabus not found")
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id", ""),
        "filename": doc.get("filename", ""),
        "raw_text": doc.get("raw_text", ""),
        "topics": doc.get("topics", []),
        "created_at": doc.get("created_at", ""),
    }
