from pydantic import BaseModel
from enum import Enum


class BloomLevel(str, Enum):
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"


class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class QuestionReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class FinalPaperStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"


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


class SubQuestion(BaseModel):
    label: str = ""
    text: str
    marks: int = 0
    model_answer: str = ""
    bank_id: str = ""


class PaperQuestion(BaseModel):
    question_number: int
    question_text: str
    sub_questions: list[SubQuestion] = []
    alternative_question_text: str = ""
    alternative_sub_questions: list[SubQuestion] = []
    marks: int
    bloom_level: str
    topic: str
    model_answer: str = ""
    unit: str = ""
    bank_id: str = ""
    source_bank_ids: list[str] = []
    or_with_next: bool = False


class FinalPaperOut(BaseModel):
    id: str
    syllabus_id: str
    exam_title: str
    total_marks: int
    duration_minutes: int
    questions: list[PaperQuestion]
    status: FinalPaperStatus = FinalPaperStatus.DRAFT
    finalized_at: str | None = None
    created_at: str


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


class QuestionBankItem(BaseModel):
    id: str = ""
    question: str
    unit: str
    topic: str = ""
    bloom_level: BloomLevel
    marks: int = 0
    difficulty: str = "medium"
    status: QuestionReviewStatus = QuestionReviewStatus.PENDING
    source_context: str | None = None
    created_at: str = ""


class QuestionBankUpdateRequest(BaseModel):
    question: str | None = None
    status: QuestionReviewStatus | None = None


class QuestionBankCreateRequest(BaseModel):
    syllabus_id: str


class DocumentOut(BaseModel):
    id: str
    syllabus_id: str
    file_name: str
    file_type: str
    uploaded_at: str


class QuestionPaperTemplateSection(BaseModel):
    name: str
    bloom_level: BloomLevel
    num_questions: int


class QuestionPaperTemplate(BaseModel):
    syllabus_id: str
    title: str = "Examination"
    sections: list[QuestionPaperTemplateSection]


class PaperTemplateSubPart(BaseModel):
    label: str = ""
    marks: int = 0


class PaperTemplateOption(BaseModel):
    subparts: list[PaperTemplateSubPart] = []


class PaperTemplateQuestionGroup(BaseModel):
    question_number: int
    unit_hint: str = ""
    marks: int = 20
    primary: PaperTemplateOption
    alternative: PaperTemplateOption | None = None
    or_with_next: bool = False


class PaperTemplateBlueprint(BaseModel):
    title: str = "Examination"
    total_marks: int = 0
    duration_minutes: int = 180
    question_groups: list[PaperTemplateQuestionGroup]


class PaperTemplateValidationIssue(BaseModel):
    level: str = "error"
    message: str
    question_number: int | None = None
    field: str = ""


class PaperTemplateValidationResult(BaseModel):
    is_valid: bool = False
    issues: list[PaperTemplateValidationIssue] = []


class PaperTemplateOut(BaseModel):
    id: str
    syllabus_id: str
    file_name: str
    uploaded_at: str
    blueprint: PaperTemplateBlueprint
    validation: PaperTemplateValidationResult


class PaperTemplateUpdateRequest(BaseModel):
    blueprint: PaperTemplateBlueprint


class TemplatePaperGenerationRequest(BaseModel):
    syllabus_id: str


class FinalPaperMetadataUpdateRequest(BaseModel):
    exam_title: str | None = None
    total_marks: int | None = None
    duration_minutes: int | None = None


class FinalPaperQuestionUpdateRequest(BaseModel):
    question_text: str | None = None
    sub_questions: list[SubQuestion] | None = None
    alternative_question_text: str | None = None
    alternative_sub_questions: list[SubQuestion] | None = None
    marks: int | None = None
    bloom_level: str | None = None
    topic: str | None = None
    unit: str | None = None
    or_with_next: bool | None = None


class FinalPaperFinalizeRequest(BaseModel):
    status: FinalPaperStatus = FinalPaperStatus.FINALIZED


class FinalPaperQuestionReplaceRequest(BaseModel):
    slot: str = "primary"
