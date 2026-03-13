import logging
from functools import lru_cache
from pathlib import Path
from typing import List

from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

_VECTOR_ROOT = Path(__file__).resolve().parents[2] / "data" / "vectorstores"


@lru_cache()
def get_embeddings() -> HuggingFaceEmbeddings:
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info("Loading embeddings model %s", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)


@lru_cache()
def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )


def _collection_name(syllabus_id: str) -> str:
    safe = ''.join(ch if ch.isalnum() else '_' for ch in syllabus_id)
    return f"syllabus_{safe}"


def _persist_directory(syllabus_id: str) -> Path:
    path = _VECTOR_ROOT / syllabus_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _document_chunk_ids(syllabus_id: str, document_id: str, count: int) -> list[str]:
    return [f"{syllabus_id}:{document_id}:{idx}" for idx in range(count)]


def _get_vector_store(syllabus_id: str) -> Chroma:
    persist_directory = str(_persist_directory(syllabus_id))
    return Chroma(
        collection_name=_collection_name(syllabus_id),
        embedding_function=get_embeddings(),
        persist_directory=persist_directory,
        client_settings=ChromaSettings(
            is_persistent=True,
            persist_directory=persist_directory,
            anonymized_telemetry=False,
        ),
    )


def upsert_syllabus_documents(syllabus_id: str, document_id: str, documents: List[Document]) -> int:
    """Split and persist a document's chunks into the syllabus vector store."""
    if not documents:
        return 0

    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    if not chunks:
        return 0

    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,
            "syllabus_id": syllabus_id,
            "document_id": document_id,
            "chunk_index": index,
        }

    vector_store = _get_vector_store(syllabus_id)
    vector_store.add_documents(
        documents=chunks,
        ids=_document_chunk_ids(syllabus_id, document_id, len(chunks)),
    )
    logger.info("Indexed %d chunks for document %s in syllabus %s", len(chunks), document_id, syllabus_id)
    return len(chunks)


def get_retriever_for_syllabus(syllabus_id: str, k: int = 4):
    """Load the persistent syllabus vector store and return a retriever if indexed data exists."""
    persist_directory = _persist_directory(syllabus_id)
    if not persist_directory.exists():
        return None

    vector_store = _get_vector_store(syllabus_id)
    if vector_store._collection.count() == 0:
        return None

    return vector_store.as_retriever(search_kwargs={"k": k})
