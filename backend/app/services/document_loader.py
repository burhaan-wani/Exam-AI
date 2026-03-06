import logging
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders.base import Document

from app.database import documents_collection

logger = logging.getLogger(__name__)


def _load_file_to_documents(temp_path: str, file_type: str) -> List[Document]:
    if file_type.lower() == "pdf":
        loader = PyPDFLoader(temp_path)
    elif file_type.lower() in {"docx", "doc"}:
        loader = Docx2txtLoader(temp_path)
    else:
        loader = TextLoader(temp_path, encoding="utf-8")
    return loader.load()


async def save_reference_documents(
    syllabus_id: str,
    file_name: str,
    file_type: str,
    temp_path: str,
) -> str:
    """
    Persist a reference document entry for a syllabus.
    The actual embeddings / vector store handling is done separately.
    """
    doc = {
        "syllabus_id": syllabus_id,
        "file_name": file_name,
        "file_type": file_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await documents_collection.insert_one(doc)
    doc_id = str(result.inserted_id)

    logger.info("Stored reference document %s for syllabus %s", file_name, syllabus_id)
    return doc_id

