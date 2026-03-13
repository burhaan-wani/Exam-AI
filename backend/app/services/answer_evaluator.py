"""
Answer Evaluator Service
Orchestrates the evaluation chain for student descriptive answers.
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.database import (
    student_answers_collection,
    final_question_paper_collection,
    evaluation_results_collection,
)
from app.chains.evaluation_chain import evaluate_answer

logger = logging.getLogger(__name__)


async def evaluate_student_submission(answer_id: str) -> dict:
    """Evaluate all answers in a student submission."""
    submission = await student_answers_collection.find_one({"_id": ObjectId(answer_id)})
    if not submission:
        raise ValueError(f"Student answer {answer_id} not found")

    paper = await final_question_paper_collection.find_one(
        {"_id": ObjectId(submission["paper_id"])}
    )
    if not paper:
        raise ValueError(f"Paper {submission['paper_id']} not found")

    paper_questions = {q["question_number"]: q for q in paper.get("questions", [])}
    question_scores = []
    total_awarded = 0.0
    total_max = 0

    for answer_item in submission.get("answers", []):
        q_num = answer_item["question_number"]
        student_text = answer_item["answer_text"]

        paper_q = paper_questions.get(q_num)
        if not paper_q:
            logger.warning(f"Question number {q_num} not found in paper")
            continue

        max_marks = paper_q.get("marks", 0)
        model_answer = paper_q.get("model_answer") or paper_q.get("question_text", "")
        bloom_level = paper_q.get("bloom_level", "Remember")

        try:
            eval_result = await evaluate_answer(
                question_text=paper_q.get("question_text", ""),
                model_answer=model_answer,
                student_answer=student_text,
                max_marks=max_marks,
                bloom_level=bloom_level,
            )
        except Exception as e:
            logger.error(f"Evaluation failed for Q{q_num}: {e}")
            eval_result = {
                "awarded_marks": 0,
                "semantic_similarity": 0,
                "completeness": 0,
                "bloom_alignment": 0,
                "reasoning": f"Evaluation error: {str(e)}",
                "feedback": "Could not evaluate this answer due to a system error.",
            }

        score = {
            "question_number": q_num,
            "max_marks": max_marks,
            "awarded_marks": eval_result.get("awarded_marks", 0),
            "semantic_similarity": eval_result.get("semantic_similarity", 0),
            "completeness": eval_result.get("completeness", 0),
            "bloom_alignment": eval_result.get("bloom_alignment", 0),
            "reasoning": eval_result.get("reasoning", ""),
            "feedback": eval_result.get("feedback", ""),
        }
        question_scores.append(score)
        total_awarded += score["awarded_marks"]
        total_max += max_marks

    percentage = round((total_awarded / total_max * 100), 2) if total_max > 0 else 0.0

    eval_doc = {
        "answer_id": answer_id,
        "paper_id": submission["paper_id"],
        "user_id": submission.get("user_id", ""),
        "student_name": submission.get("student_name", ""),
        "question_scores": question_scores,
        "total_marks": total_awarded,
        "max_marks": total_max,
        "percentage": percentage,
        "overall_feedback": _generate_overall_feedback(percentage, question_scores),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await evaluation_results_collection.insert_one(eval_doc)
    eval_doc["_id"] = result.inserted_id
    logger.info(f"Evaluation complete: {total_awarded}/{total_max} ({percentage}%)")
    return eval_doc


def _generate_overall_feedback(percentage: float, scores: list[dict]) -> str:
    """Generate overall feedback summary."""
    if percentage >= 90:
        grade = "Excellent"
    elif percentage >= 75:
        grade = "Very Good"
    elif percentage >= 60:
        grade = "Good"
    elif percentage >= 40:
        grade = "Satisfactory"
    else:
        grade = "Needs Improvement"

    weak = [s for s in scores if s["awarded_marks"] < s["max_marks"] * 0.5]
    weak_topics = ", ".join(f"Q{s['question_number']}" for s in weak[:3])

    feedback = f"Overall Grade: {grade} ({percentage}%)."
    if weak_topics:
        feedback += f" Focus on improving: {weak_topics}."
    return feedback


def format_eval_out(doc: dict) -> dict:
    """Format evaluation result for API response."""
    return {
        "id": str(doc["_id"]),
        "answer_id": doc.get("answer_id", ""),
        "paper_id": doc.get("paper_id", ""),
        "student_name": doc.get("student_name", ""),
        "question_scores": doc.get("question_scores", []),
        "total_marks": doc.get("total_marks", 0),
        "max_marks": doc.get("max_marks", 0),
        "percentage": doc.get("percentage", 0),
        "overall_feedback": doc.get("overall_feedback", ""),
        "evaluated_at": doc.get("evaluated_at", ""),
    }
