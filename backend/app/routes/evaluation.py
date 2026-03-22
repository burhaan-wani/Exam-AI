import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import (
    evaluation_results_collection,
    final_question_paper_collection,
    student_answers_collection,
    syllabus_collection,
)
from app.dependencies.auth import require_student, require_teacher
from app.models.schemas import EvaluateRequest, FinalPaperStatus, StudentAnswerSubmit
from app.services.answer_evaluator import evaluate_student_submission, format_eval_out

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_student_submission_or_404(answer_id: str) -> dict:
    try:
        doc = await student_answers_collection.find_one({"_id": ObjectId(answer_id)})
    except Exception:
        raise HTTPException(400, "Invalid answer ID")

    if not doc:
        raise HTTPException(404, "Answer submission not found")
    return doc


async def _get_student_evaluation_or_404(eval_id: str) -> dict:
    try:
        doc = await evaluation_results_collection.find_one({"_id": ObjectId(eval_id)})
    except Exception:
        raise HTTPException(400, "Invalid evaluation ID")

    if not doc:
        raise HTTPException(404, "Evaluation result not found")
    return doc


async def _get_paper_or_404(paper_id: str) -> dict:
    try:
        doc = await final_question_paper_collection.find_one({"_id": ObjectId(paper_id)})
    except Exception:
        raise HTTPException(400, "Invalid paper ID")

    if not doc:
        raise HTTPException(404, "Question paper not found")
    return doc


async def _ensure_teacher_owns_paper(paper_id: str, teacher_id: str) -> None:
    paper = await _get_paper_or_404(paper_id)
    syllabus_id = paper.get("syllabus_id", "")
    try:
        syllabus = await syllabus_collection.find_one({"_id": ObjectId(syllabus_id), "user_id": teacher_id})
    except Exception:
        raise HTTPException(400, "Invalid syllabus ID on paper")

    if not syllabus:
        raise HTTPException(403, "You do not have access to this paper")


@router.post("/submit")
async def submit_student_answers(
    body: StudentAnswerSubmit,
    current_user: dict = Depends(require_student),
):
    """Submit student answers for a question paper."""
    paper = await _get_paper_or_404(body.paper_id)
    if paper.get("status") != FinalPaperStatus.FINALIZED.value:
        raise HTTPException(403, "This paper is not yet open for student submissions")

    try:
        doc = {
            "paper_id": body.paper_id,
            "student_name": body.student_name,
            "user_id": current_user["id"],
            "answers": [a.model_dump() for a in body.answers],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await student_answers_collection.insert_one(doc)
        logger.info("Student submission received: %s, %d answers", body.student_name, len(body.answers))
        return {
            "id": str(result.inserted_id),
            "paper_id": body.paper_id,
            "student_name": body.student_name,
            "answers": doc["answers"],
            "submitted_at": doc["submitted_at"],
        }
    except Exception as e:
        logger.error("Failed to save submission: %s", e)
        raise HTTPException(500, f"Failed to save submission: {str(e)}")


@router.get("/{answer_id}")
async def get_student_submission(
    answer_id: str,
    current_user: dict = Depends(require_student),
):
    """Get the current student's answer submission."""
    doc = await _get_student_submission_or_404(answer_id)
    if doc.get("user_id") != current_user["id"]:
        raise HTTPException(403, "You do not have access to this submission")

    return {
        "id": str(doc["_id"]),
        "paper_id": doc.get("paper_id", ""),
        "student_name": doc.get("student_name", ""),
        "answers": doc.get("answers", []),
        "submitted_at": doc.get("submitted_at", ""),
    }


@router.post("/evaluate")
async def evaluate_answers(
    body: EvaluateRequest,
    current_user: dict = Depends(require_student),
):
    """Evaluate the current student's answer submission using the LLM pipeline."""
    submission = await _get_student_submission_or_404(body.answer_id)
    if submission.get("user_id") != current_user["id"]:
        raise HTTPException(403, "You do not have access to this submission")

    try:
        result = await evaluate_student_submission(body.answer_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error("Evaluation failed: %s", e)
        raise HTTPException(500, f"Evaluation failed: {str(e)}")

    return format_eval_out(result)


@router.get("/results/{eval_id}")
async def get_evaluation_result(
    eval_id: str,
    current_user: dict = Depends(require_student),
):
    """Get evaluation results for the current student's submission."""
    doc = await _get_student_evaluation_or_404(eval_id)
    if doc.get("user_id") != current_user["id"]:
        raise HTTPException(403, "You do not have access to this evaluation")
    return format_eval_out(doc)


@router.get("/by-submission/{answer_id}")
async def get_evaluation_by_submission(
    answer_id: str,
    current_user: dict = Depends(require_student),
):
    """Get evaluation results for the current student's submission ID."""
    submission = await _get_student_submission_or_404(answer_id)
    if submission.get("user_id") != current_user["id"]:
        raise HTTPException(403, "You do not have access to this submission")

    doc = await evaluation_results_collection.find_one({"answer_id": answer_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(404, "No evaluation found for this submission")

    return format_eval_out(doc)


@router.get("/by-paper/{paper_id}")
async def list_evaluations_by_paper(
    paper_id: str,
    current_user: dict = Depends(require_teacher),
):
    """List evaluations for a teacher-owned paper."""
    await _ensure_teacher_owns_paper(paper_id, current_user["id"])

    try:
        cursor = evaluation_results_collection.find({"paper_id": paper_id})
        docs = await cursor.to_list(length=100)
    except Exception as e:
        logger.error("Failed to list evaluations: %s", e)
        raise HTTPException(500, "Failed to list evaluations")

    return [format_eval_out(d) for d in docs]
