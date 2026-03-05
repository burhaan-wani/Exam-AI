"""
Question Generation Service
Orchestrates LangChain generation chain and stores results in MongoDB.
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.database import generated_questions_collection, question_blueprint_collection
from app.chains.generation_chain import generate_questions as llm_generate
from app.models.schemas import BloomLevel, QuestionStatus

logger = logging.getLogger(__name__)


async def generate_questions_for_blueprint(blueprint_id: str) -> list[dict]:
    """Generate all questions for a given blueprint configuration."""
    blueprint = await question_blueprint_collection.find_one({"_id": ObjectId(blueprint_id)})
    if not blueprint:
        raise ValueError(f"Blueprint {blueprint_id} not found")

    syllabus_id = blueprint["syllabus_id"]
    all_questions = []

    for config in blueprint["configs"]:
        topic = config["topic"]
        bloom_level = BloomLevel(config["bloom_level"])
        difficulty = config.get("difficulty", "medium")
        num_questions = config.get("num_questions", 2)
        marks_per_question = config.get("marks_per_question", 5)

        try:
            raw_questions = await llm_generate(
                topic=topic,
                bloom_level=bloom_level,
                difficulty=difficulty,
                num_questions=num_questions,
                marks_per_question=marks_per_question,
            )
        except Exception as e:
            logger.error(f"Generation failed for topic={topic}: {e}")
            continue

        for q in raw_questions:
            doc = {
                "syllabus_id": syllabus_id,
                "blueprint_id": blueprint_id,
                "topic": topic,
                "bloom_level": bloom_level.value,
                "difficulty": difficulty,
                "question_text": q.get("question_text", ""),
                "sub_questions": q.get("sub_questions", []),
                "marks": q.get("marks", marks_per_question),
                "model_answer": q.get("model_answer", ""),
                "status": QuestionStatus.PENDING.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            result = await generated_questions_collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            all_questions.append(doc)

    logger.info(f"Generated {len(all_questions)} total questions for blueprint {blueprint_id}")
    return all_questions


def format_question_out(doc: dict) -> dict:
    """Format a MongoDB question document for API response."""
    return {
        "id": str(doc["_id"]),
        "syllabus_id": doc.get("syllabus_id", ""),
        "blueprint_id": doc.get("blueprint_id", ""),
        "topic": doc.get("topic", ""),
        "bloom_level": doc.get("bloom_level", "Remember"),
        "difficulty": doc.get("difficulty", "medium"),
        "question_text": doc.get("question_text", ""),
        "sub_questions": doc.get("sub_questions", []),
        "marks": doc.get("marks", 0),
        "model_answer": doc.get("model_answer", ""),
        "status": doc.get("status", "pending"),
        "created_at": doc.get("created_at", ""),
    }
