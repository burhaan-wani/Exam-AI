import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from bson import ObjectId

from app.database import syllabus_collection
from app.utils.file_parser import extract_text
from app.services.syllabus_processor import extract_topics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_syllabus(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous"),
):
    """Upload a syllabus file and extract topics."""
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    try:
        raw_text = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Extract topics via LLM (OpenRouter)
    try:
        topics = await extract_topics(raw_text)
    except ValueError as e:
        raise HTTPException(400, str(e))

    doc = {
        "user_id": user_id,
        "filename": filename,
        "raw_text": raw_text,
        "topics": topics,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await syllabus_collection.insert_one(doc)
    logger.info(f"Syllabus uploaded: {filename}, {len(topics)} topics extracted")

    return {
        "id": str(result.inserted_id),
        "filename": filename,
        "topics": topics,
        "topic_count": len(topics),
    }


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
    """Get full syllabus details."""
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
