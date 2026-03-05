import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_indexes
from app.utils.logger import setup_logging
from app.routes import syllabus, questions, hitl, paper, evaluation, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.getLogger(__name__).info("Starting Exam AI backend...")
    await init_indexes()
    yield
    logging.getLogger(__name__).info("Shutting down Exam AI backend.")


app = FastAPI(
    title="Exam AI",
    description="AI-powered Question Paper Generation & Answer Evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(syllabus.router, prefix="/api/syllabus", tags=["Syllabus"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
app.include_router(hitl.router, prefix="/api/hitl", tags=["HITL"])
app.include_router(paper.router, prefix="/api/paper", tags=["Paper"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
