import logging
from functools import lru_cache
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)


@lru_cache()
def get_embeddings() -> HuggingFaceEmbeddings:
    # Lightweight general-purpose sentence-transformer
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info("Loading embeddings model %s", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)


def build_vector_store_from_documents(documents: List[Document]) -> Tuple[FAISS, int]:
    """Create an in-memory FAISS index from a list of LangChain Documents."""
    if not documents:
        raise ValueError("No documents provided for vector store")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)
    logger.info("Split %d documents into %d chunks for RAG", len(documents), len(chunks))

    embeddings = get_embeddings()
    vs = FAISS.from_documents(chunks, embeddings)
    return vs, len(chunks)


def get_retriever_from_vector_store(vs: FAISS, k: int = 4):
    """Return a retriever interface from an existing FAISS vector store."""
    return vs.as_retriever(search_kwargs={"k": k})

