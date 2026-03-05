import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import generated_questions_collection, hitl_feedback_collection
from app.models.schemas import HITLAction, QuestionStatus, BloomLevel
from app.chains.refinement_chain import refine_question
from app.services.question_generator import format_question_out

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/review")
async def review_question(body: HITLAction):
    """Process a HITL review action on a question."""
    question = await generated_questions_collection.find_one({"_id": ObjectId(body.question_id)})
    if not question:
        raise HTTPException(404, "Question not found")

    # Record feedback
    feedback_doc = {
        "question_id": body.question_id,
        "action": body.action.value,
        "modified_text": body.modified_text,
        "feedback_note": body.feedback_note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await hitl_feedback_collection.insert_one(feedback_doc)

    # Process action
    if body.action == QuestionStatus.APPROVED:
        await generated_questions_collection.update_one(
            {"_id": ObjectId(body.question_id)},
            {"$set": {"status": "approved"}},
        )
        logger.info(f"Question {body.question_id} approved")

    elif body.action == QuestionStatus.REJECTED:
        await generated_questions_collection.update_one(
            {"_id": ObjectId(body.question_id)},
            {"$set": {"status": "rejected"}},
        )
        logger.info(f"Question {body.question_id} rejected")

    elif body.action == QuestionStatus.MODIFIED:
        # Teacher directly modified the text
        update = {"status": "approved", "question_text": body.modified_text or question["question_text"]}
        await generated_questions_collection.update_one(
            {"_id": ObjectId(body.question_id)},
            {"$set": update},
        )
        logger.info(f"Question {body.question_id} modified and approved")

    elif body.action == QuestionStatus.REGENERATE:
        # Use LLM to refine based on feedback
        bloom_level = BloomLevel(question.get("bloom_level", "Remember"))
        try:
            refined = await refine_question(
                original_question=question["question_text"],
                feedback=body.feedback_note or "Please improve this question.",
                bloom_level=bloom_level,
            )
            update = {
                "status": "pending",
                "question_text": refined.get("question_text", question["question_text"]),
                "sub_questions": refined.get("sub_questions", question.get("sub_questions", [])),
                "model_answer": refined.get("model_answer", question.get("model_answer", "")),
            }
            await generated_questions_collection.update_one(
                {"_id": ObjectId(body.question_id)},
                {"$set": update},
            )
            logger.info(f"Question {body.question_id} regenerated via LLM")
        except Exception as e:
            logger.error(f"Regeneration failed: {e}")
            raise HTTPException(500, f"Regeneration failed: {str(e)}")

    # Return updated question
    updated = await generated_questions_collection.find_one({"_id": ObjectId(body.question_id)})
    return format_question_out(updated)


@router.get("/feedback/{question_id}")
async def get_feedback_history(question_id: str):
    """Get all HITL feedback for a question."""
    cursor = hitl_feedback_collection.find({"question_id": question_id})
    docs = await cursor.to_list(length=50)
    return [
        {
            "id": str(d["_id"]),
            "question_id": d.get("question_id", ""),
            "action": d.get("action", ""),
            "modified_text": d.get("modified_text"),
            "feedback_note": d.get("feedback_note"),
            "created_at": d.get("created_at", ""),
        }
        for d in docs
    ]
