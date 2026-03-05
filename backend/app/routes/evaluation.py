import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import student_answers_collection, evaluation_results_collection
from app.models.schemas import StudentAnswerSubmit, EvaluateRequest
from app.services.answer_evaluator import evaluate_student_submission, format_eval_out

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/submit")
async def submit_student_answers(body: StudentAnswerSubmit):
    """Submit student answers for a question paper."""
    try:
        doc = {
            "paper_id": body.paper_id,
            "student_name": body.student_name,
            "answers": [a.model_dump() for a in body.answers],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await student_answers_collection.insert_one(doc)
        logger.info(f"Student submission received: {body.student_name}, {len(body.answers)} answers")
        return {
            "id": str(result.inserted_id),
            "paper_id": body.paper_id,
            "student_name": body.student_name,
            "answers": doc["answers"],
            "submitted_at": doc["submitted_at"],
        }
    except Exception as e:
        logger.error(f"Failed to save submission: {e}")
        raise HTTPException(500, f"Failed to save submission: {str(e)}")


@router.get("/{answer_id}")
async def get_student_submission(answer_id: str):
    """Get a student's answer submission."""
    try:
        doc = await student_answers_collection.find_one({"_id": ObjectId(answer_id)})
    except Exception:
        raise HTTPException(400, "Invalid answer ID")

    if not doc:
        raise HTTPException(404, "Answer submission not found")

    return {
        "id": str(doc["_id"]),
        "paper_id": doc.get("paper_id", ""),
        "student_name": doc.get("student_name", ""),
        "answers": doc.get("answers", []),
        "submitted_at": doc.get("submitted_at", ""),
    }


@router.post("/evaluate")
async def evaluate_answers(body: EvaluateRequest):
    """Evaluate a student's answer submission using LLM."""
    try:
        result = await evaluate_student_submission(body.answer_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(500, f"Evaluation failed: {str(e)}")

    return format_eval_out(result)


@router.get("/results/{eval_id}")
async def get_evaluation_result(eval_id: str):
    """Get evaluation results for a student submission."""
    try:
        doc = await evaluation_results_collection.find_one({"_id": ObjectId(eval_id)})
    except Exception:
        raise HTTPException(400, "Invalid evaluation ID")

    if not doc:
        raise HTTPException(404, "Evaluation result not found")

    return format_eval_out(doc)


@router.get("/by-submission/{answer_id}")
async def get_evaluation_by_submission(answer_id: str):
    """Get evaluation results by answer submission ID."""
    try:
        doc = await evaluation_results_collection.find_one({"answer_id": answer_id})
    except Exception as e:
        logger.error(f"Failed to get evaluation: {e}")
        raise HTTPException(500, "Failed to get evaluation")

    if not doc:
        raise HTTPException(404, "No evaluation found for this submission")

    return format_eval_out(doc)


@router.get("/by-paper/{paper_id}")
async def list_evaluations_by_paper(paper_id: str):
    """List all evaluations for a question paper."""
    try:
        cursor = evaluation_results_collection.find({"paper_id": paper_id})
        docs = await cursor.to_list(length=100)
    except Exception as e:
        logger.error(f"Failed to list evaluations: {e}")
        raise HTTPException(500, "Failed to list evaluations")

    return [format_eval_out(d) for d in docs]
