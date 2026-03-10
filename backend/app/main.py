import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from openai import AuthenticationError as OpenAIAuthError

from app.config import get_settings
from app.database import init_indexes
from app.utils.logger import setup_logging
from app.routes import syllabus, paper, evaluation, auth, question_bank

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

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_AUTH_MESSAGE = (
    "OpenRouter authentication failed (401). "
    "Check OPENROUTER_API_KEY in backend/.env: get or regenerate a key at https://openrouter.ai/keys "
    "and ensure your account has credits."
)


@app.exception_handler(OpenAIAuthError)
async def openrouter_auth_error(_request, exc):
    return JSONResponse(
        status_code=502,
        content={"detail": OPENROUTER_AUTH_MESSAGE},
    )


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(syllabus.router, prefix="/api/syllabus", tags=["Syllabus"])
app.include_router(paper.router, prefix="/api/paper", tags=["Paper"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(
    question_bank.router,
    prefix="/api",
    tags=["Question Bank & Paper Generation"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
