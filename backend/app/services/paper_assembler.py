"""
Question Paper Assembly Service
Compiles approved questions into a final formatted question paper.
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.database import (
    generated_questions_collection,
    question_blueprint_collection,
    final_question_paper_collection,
)

logger = logging.getLogger(__name__)


async def assemble_paper(blueprint_id: str) -> dict:
    """Assemble a final question paper from approved questions."""
    blueprint = await question_blueprint_collection.find_one({"_id": ObjectId(blueprint_id)})
    if not blueprint:
        raise ValueError(f"Blueprint {blueprint_id} not found")

    # Fetch all approved questions for this blueprint
    cursor = generated_questions_collection.find({
        "blueprint_id": blueprint_id,
        "status": "approved",
    })
    questions_raw = await cursor.to_list(length=200)

    if not questions_raw:
        raise ValueError("No approved questions found. Please review and approve questions first.")

    # Build paper questions with numbering
    paper_questions = []
    total_marks = 0
    for i, q in enumerate(questions_raw, start=1):
        pq = {
            "question_number": i,
            "question_text": q.get("question_text", ""),
            "sub_questions": q.get("sub_questions", []),
            "marks": q.get("marks", 0),
            "bloom_level": q.get("bloom_level", ""),
            "topic": q.get("topic", ""),
            # Preserve model answers so evaluation can use them later
            "model_answer": q.get("model_answer", ""),
        }
        paper_questions.append(pq)
        total_marks += pq["marks"]

    paper_doc = {
        "syllabus_id": blueprint.get("syllabus_id", ""),
        "blueprint_id": blueprint_id,
        "exam_title": blueprint.get("exam_title", "Examination"),
        "total_marks": total_marks,
        "duration_minutes": blueprint.get("duration_minutes", 180),
        "questions": paper_questions,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await final_question_paper_collection.insert_one(paper_doc)
    paper_doc["_id"] = result.inserted_id
    logger.info(f"Assembled paper with {len(paper_questions)} questions, total_marks={total_marks}")
    return paper_doc


def format_paper_out(doc: dict) -> dict:
    """Format a paper document for API response."""
    return {
        "id": str(doc["_id"]),
        "syllabus_id": doc.get("syllabus_id", ""),
        "blueprint_id": doc.get("blueprint_id", ""),
        "exam_title": doc.get("exam_title", ""),
        "total_marks": doc.get("total_marks", 0),
        "duration_minutes": doc.get("duration_minutes", 180),
        "questions": doc.get("questions", []),
        "created_at": doc.get("created_at", ""),
    }
