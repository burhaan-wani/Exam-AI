from __future__ import annotations

from datetime import datetime, timezone
from fastapi import UploadFile

from app.database import documents_collection
from app.utils.file_parser import extract_text


async def save_document(syllabus_id: str, file: UploadFile) -> dict:
    file_bytes = await file.read()
    filename = file.filename or "unknown"
    content = extract_text(file_bytes, filename)
    file_type = filename.split(".")[-1].lower() if "." in filename else "txt"

    doc = {
        "syllabus_id": syllabus_id,
        "file_name": filename,
        "file_type": file_type,
        "content": content,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await documents_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

