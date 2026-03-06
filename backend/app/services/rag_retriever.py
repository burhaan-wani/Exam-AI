import logging
from typing import List

from langchain_core.documents import Document

from app.services.vector_store import build_vector_store_from_documents, get_retriever_from_vector_store

logger = logging.getLogger(__name__)


async def build_retriever_for_unit(documents: List[Document]):
    """
    Build a simple in-memory retriever over all provided documents.
    In a more advanced version, this could be cached per syllabus/unit.
    """
    if not documents:
        return None

    vs, chunk_count = build_vector_store_from_documents(documents)
    logger.info("Built FAISS vector store with %d chunks", chunk_count)
    return get_retriever_from_vector_store(vs)

