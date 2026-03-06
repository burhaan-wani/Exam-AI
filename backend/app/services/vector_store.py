import os
from app.config import get_settings

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS


settings = get_settings()


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.openrouter_embedding_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )


def get_vector_store(collection_name: str = "exam_ai_docs"):
    backend = (settings.vector_store_backend or "chroma").lower().strip()
    embeddings = get_embeddings()

    if backend == "faiss":
        # In-memory FAISS (caller responsible for persistence if desired)
        return FAISS.from_texts(texts=[], embedding=embeddings)

    # Default: persistent Chroma
    persist_dir = settings.chroma_persist_dir or "./data/chroma"
    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

