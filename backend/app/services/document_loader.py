import logging
from datetime import datetime, timezone
from typing import List

from langchain.schema import Document

from app.database import documents_collection

logger = logging.getLogger(__name__)


def build_langchain_documents(
    syllabus_id: str,
    file_name: str,
    file_type: str,
    content: str,
    document_id: str = "",
) -> List[Document]:
    """Create LangChain documents from stored reference content."""
    if not content.strip():
        return []

    return [
        Document(
            page_content=content,
            metadata={
                "syllabus_id": syllabus_id,
                "document_id": document_id,
                "file_name": file_name,
                "file_type": file_type,
            },
        )
    ]


async def save_reference_document(
    syllabus_id: str,
    file_name: str,
    file_type: str,
    content: str,
) -> dict:
    """Persist reference material metadata and extracted text."""
    uploaded_at = datetime.now(timezone.utc).isoformat()
    doc = {
        "syllabus_id": syllabus_id,
        "file_name": file_name,
        "file_type": file_type,
        "content": content,
        "uploaded_at": uploaded_at,
        "indexed_at": None,
        "chunk_count": 0,
    }
    result = await documents_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Stored reference document %s for syllabus %s", file_name, syllabus_id)
    return doc


async def mark_reference_document_indexed(document_id: str, chunk_count: int) -> None:
    indexed_at = datetime.now(timezone.utc).isoformat()
    await documents_collection.update_one(
        {"_id": document_id if hasattr(document_id, 'binary') else document_id},
        {"$set": {"indexed_at": indexed_at, "chunk_count": chunk_count}},
    )


async def load_reference_documents_for_syllabus(syllabus_id: str) -> List[Document]:
    """Load all saved reference materials for a syllabus as LangChain documents."""
    cursor = documents_collection.find({"syllabus_id": syllabus_id})
    docs = await cursor.to_list(length=200)

    loaded: List[Document] = []
    for doc in docs:
        loaded.extend(
            build_langchain_documents(
                syllabus_id=syllabus_id,
                file_name=doc.get("file_name", ""),
                file_type=doc.get("file_type", ""),
                content=doc.get("content", ""),
                document_id=str(doc.get("_id", "")),
            )
        )
    return loaded
