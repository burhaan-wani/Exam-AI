from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class BloomLevel(str, Enum):
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"


class QuestionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    REGENERATE = "regenerate"


class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


# ── User ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.TEACHER


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Syllabus ───────────────────────────────────────────────────────────────────

class TopicItem(BaseModel):
    name: str
    unit: str = ""
    subtopics: list[str] = []


class SyllabusOut(BaseModel):
    id: str
    user_id: str
    filename: str
    raw_text: str
    topics: list[TopicItem] = []
    created_at: str


class SyllabusListItem(BaseModel):
    id: str
    filename: str
    topic_count: int
    created_at: str


# ── Bloom Configuration ───────────────────────────────────────────────────────

class BloomConfig(BaseModel):
    topic: str
    bloom_level: BloomLevel
    num_questions: int = 2
    marks_per_question: int = 5
    difficulty: str = "medium"  # easy, medium, hard


class BlueprintCreate(BaseModel):
    syllabus_id: str
    exam_title: str = "Examination"
    total_marks: int = 100
    duration_minutes: int = 180
    configs: list[BloomConfig]


class BlueprintOut(BaseModel):
    id: str
    syllabus_id: str
    exam_title: str
    total_marks: int
    duration_minutes: int
    configs: list[BloomConfig]
    created_at: str


# ── Generated Questions ───────────────────────────────────────────────────────

class SubQuestion(BaseModel):
    label: str = ""  # e.g. "(a)", "(b)"
    text: str
    marks: int = 0
    model_answer: str = ""


class GeneratedQuestion(BaseModel):
    id: str = ""
    syllabus_id: str = ""
    blueprint_id: str = ""
    topic: str
    bloom_level: BloomLevel
    difficulty: str = "medium"
    question_text: str
    sub_questions: list[SubQuestion] = []
    marks: int
    model_answer: str = ""
    status: QuestionStatus = QuestionStatus.PENDING
    created_at: str = ""


class QuestionGenerateRequest(BaseModel):
    blueprint_id: str


# ── HITL Feedback ──────────────────────────────────────────────────────────────

class HITLAction(BaseModel):
    question_id: str
    action: QuestionStatus  # approved, rejected, modified, regenerate
    modified_text: Optional[str] = None
    feedback_note: Optional[str] = None


class HITLFeedbackOut(BaseModel):
    id: str
    question_id: str
    action: str
    modified_text: Optional[str] = None
    feedback_note: Optional[str] = None
    created_at: str


# ── Final Question Paper ──────────────────────────────────────────────────────

class PaperQuestion(BaseModel):
    question_number: int
    question_text: str
    sub_questions: list[SubQuestion] = []
    marks: int
    bloom_level: str
    topic: str
    model_answer: str = ""


class FinalPaperOut(BaseModel):
    id: str
    syllabus_id: str
    blueprint_id: str
    exam_title: str
    total_marks: int
    duration_minutes: int
    questions: list[PaperQuestion]
    created_at: str


class AssemblePaperRequest(BaseModel):
    blueprint_id: str


# ── Student Answers ───────────────────────────────────────────────────────────

class AnswerItem(BaseModel):
    question_number: int
    answer_text: str


class StudentAnswerSubmit(BaseModel):
    paper_id: str
    student_name: str
    answers: list[AnswerItem]


class StudentAnswerOut(BaseModel):
    id: str
    paper_id: str
    student_name: str
    answers: list[AnswerItem]
    submitted_at: str


# ── Evaluation Results ────────────────────────────────────────────────────────

class QuestionScore(BaseModel):
    question_number: int
    max_marks: int
    awarded_marks: float
    semantic_similarity: float = 0.0
    completeness: float = 0.0
    bloom_alignment: float = 0.0
    reasoning: str = ""
    feedback: str = ""


class EvaluationResultOut(BaseModel):
    id: str
    answer_id: str
    paper_id: str
    student_name: str
    question_scores: list[QuestionScore]
    total_marks: float
    max_marks: int
    percentage: float
    overall_feedback: str = ""
    evaluated_at: str


class EvaluateRequest(BaseModel):
    answer_id: str
