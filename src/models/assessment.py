"""
Assessment Domain Models for P3 — Integrated Diagnostic Assessment
Defines AssessmentSession, Question views (safe for student clients),
Answer submission requests, and evaluation results.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

from src.models.question import QuestionType, QuestionDifficulty, CognitiveLevel


class AssessmentType(str, Enum):
    DIAGNOSTIC = "DIAGNOSTIC"
    ADAPTIVE_PRACTICE = "ADAPTIVE_PRACTICE"
    REVISION = "REVISION"


class AssessmentStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"


class AssessmentQuestionView(BaseModel):
    """
    Student-facing question representation.
    CRITICAL: Never exposes correct_option, answer_key, or explanation before evaluation.
    """
    question_id: str
    question_text: str
    question_type: QuestionType
    chapter_id: str
    topic_id: str
    concept_ids: List[str] = Field(default_factory=list)
    difficulty: QuestionDifficulty
    cognitive_level: CognitiveLevel
    marks: int
    expected_time_seconds: int
    # For MCQs: provides options dict (e.g. {'A': '...', 'B': '...'})
    options: Optional[Dict[str, str]] = None
    # For Case-Based: provides passage without answers
    passage: Optional[str] = None
    # For Assertion-Reason: provides assertion and reason statements
    assertion: Optional[str] = None
    reason: Optional[str] = None

    @classmethod
    def from_question(cls, q: Any) -> "AssessmentQuestionView":
        ak = getattr(q, "answer_key", None) or {}
        return cls(
            question_id=q.question_id,
            question_text=q.question_text,
            question_type=q.question_type,
            chapter_id=q.chapter_id,
            topic_id=q.topic_id,
            concept_ids=q.concept_ids,
            difficulty=q.difficulty,
            cognitive_level=q.cognitive_level,
            marks=q.marks,
            expected_time_seconds=q.expected_time_seconds,
            options=ak.get("options"),
            passage=ak.get("passage"),
            assertion=ak.get("assertion"),
            reason=ak.get("reason"),
        )


class SubmitAnswerRequest(BaseModel):
    """Payload for submitting a single question response."""
    question_id: str
    submitted_answer: Dict[str, Any]
    time_spent_seconds: int = Field(default=0, ge=0)
    student_id: Optional[str] = None


class AnswerEvaluationResult(BaseModel):
    """Evaluation output for an individual question answer."""
    question_id: str
    is_correct: bool
    marks_awarded: float
    max_marks: int
    feedback: str
    detected_misconceptions: List[str] = Field(default_factory=list)
    correct_answer_preview: Optional[str] = None
    explanation: Optional[str] = None


class AssessmentSession(BaseModel):
    """Active diagnostic or adaptive assessment instance."""
    assessment_id: str
    student_id: str
    assessment_type: AssessmentType
    chapter_id: Optional[str] = None
    status: AssessmentStatus
    total_questions: int
    total_marks: int
    score: float = 0.0
    questions: List[AssessmentQuestionView] = Field(default_factory=list)
    answers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class QuestionReviewItem(BaseModel):
    """Detailed post-submission review item for a student."""
    question_id: str
    question_text: str
    question_type: QuestionType
    difficulty: QuestionDifficulty
    marks: int
    marks_awarded: float
    is_correct: bool
    submitted_answer: Dict[str, Any]
    correct_answer: Any
    explanation: str
    concept_ids: List[str]
    misconceptions: List[str] = Field(default_factory=list)


class AssessmentResultSummary(BaseModel):
    """Comprehensive diagnostic result delivered after final submission."""
    assessment_id: str
    student_id: str
    assessment_type: AssessmentType
    chapter_id: Optional[str]
    status: AssessmentStatus
    total_questions: int
    answered_questions: int
    total_marks: int
    score: float
    percentage: float
    concept_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    strong_concepts: List[str] = Field(default_factory=list)
    weak_concepts: List[str] = Field(default_factory=list)
    detected_misconceptions: List[str] = Field(default_factory=list)
    recommended_next_action: Dict[str, Any] = Field(default_factory=dict)
    question_reviews: List[QuestionReviewItem] = Field(default_factory=list)
    completed_at: str
