import logging

from app.services.vector_store import get_retriever_for_syllabus

logger = logging.getLogger(__name__)


async def build_retriever_for_syllabus(syllabus_id: str):
    """Return a persistent retriever for a syllabus if reference docs have been indexed."""
    retriever = get_retriever_for_syllabus(syllabus_id)
    if retriever is None:
        logger.info("No persistent retriever available for syllabus %s", syllabus_id)
    return retriever
