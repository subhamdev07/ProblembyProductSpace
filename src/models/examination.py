"""
Examination Domain Models for P5 — CBSE Board Examination Simulation Engine
Defines ExaminationBlueprint, ExamSection, ExaminationSession, ExaminationAnswer,
SaveExamAnswerRequest/Response, and comprehensive ExaminationResultSummary schemas.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

from src.models.question import QuestionType, QuestionDifficulty, CognitiveLevel


class ExaminationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    TIMED_OUT = "TIMED_OUT"
    ABANDONED = "ABANDONED"


class ExamSectionConfig(BaseModel):
    """Configuration for an individual examination section."""
    section_name: str = Field(..., description="e.g. 'Section A'")
    section_title: str = Field(..., description="e.g. 'Multiple Choice & Assertion-Reasoning'")
    question_types: List[QuestionType]
    question_count: int
    marks_per_question: int
    total_section_marks: int
    instructions: str
    internal_choice_count: int = Field(default=0, description="Number of questions featuring internal choice")


class ExaminationBlueprint(BaseModel):
    """Standardized official or mock examination pattern blueprint."""
    blueprint_id: str
    title: str
    academic_session: str = "2026-27"
    curriculum_id: str = "CURR-CBSE-10"
    total_marks: int = 80
    duration_minutes: int = 180
    question_count: int = 39
    sections: List[ExamSectionConfig]
    unit_weightage: Dict[str, int] = Field(default_factory=dict)
    cognitive_distribution: Dict[str, float] = Field(default_factory=dict)
    general_instructions: List[str] = Field(default_factory=list)
    is_official: bool = True


class ExaminationQuestionItem(BaseModel):
    """
    Student-facing question item for the examination workspace.
    CRITICAL: Never leaks answer keys, correct options, or explanations before submission.
    """
    question_id: str
    question_number: int
    section_name: str
    question_text: str
    question_type: QuestionType
    chapter_id: str
    chapter_name: Optional[str] = None
    topic_id: Optional[str] = None
    concept_ids: List[str] = Field(default_factory=list)
    marks: int
    difficulty: QuestionDifficulty
    cognitive_level: CognitiveLevel
    options: Optional[Dict[str, str]] = None
    passage: Optional[str] = None
    assertion: Optional[str] = None
    reason: Optional[str] = None
    diagram_url: Optional[str] = None
    has_internal_choice: bool = False
    alternative_question: Optional[Dict[str, Any]] = None


class ExaminationSessionState(BaseModel):
    """Authoritative examination session state for active testing and recovery."""
    session_id: str
    student_id: str
    paper_title: str
    paper_code: str
    blueprint_id: str
    status: ExaminationStatus
    started_at: str
    expires_at: str
    remaining_time_seconds: int
    duration_minutes: int
    total_marks: int
    total_questions: int
    questions: List[ExaminationQuestionItem]
    saved_answers: Dict[str, Any] = Field(default_factory=dict)
    marked_for_review: List[str] = Field(default_factory=list)
    answered_count: int = 0
    marked_count: int = 0
    unanswered_count: int = 0
    server_time: str


class SaveExamAnswerRequest(BaseModel):
    """Payload sent by client to persist student response in real-time."""
    question_id: str
    submitted_answer: Dict[str, Any]
    is_marked_for_review: bool = False
    time_spent_seconds: int = Field(default=0, ge=0)


class SaveExamAnswerResponse(BaseModel):
    session_id: str
    question_id: str
    is_saved: bool
    is_marked_for_review: bool
    server_timestamp: str
    remaining_time_seconds: int
    answered_count: int
    unanswered_count: int
    marked_count: int


class SubmitExamRequest(BaseModel):
    student_id: str = "STU-001"
    is_timeout: bool = False


class ExamQuestionReviewItem(BaseModel):
    """Post-submission question review with marking and pedagogical explanations."""
    question_id: str
    question_number: int
    section_name: str
    question_text: str
    question_type: QuestionType
    chapter_id: str
    chapter_name: Optional[str] = None
    concept_ids: List[str] = Field(default_factory=list)
    marks: int
    marks_awarded: float
    is_correct: bool
    submitted_answer: Any
    correct_answer: Any
    explanation: str
    evaluation_feedback: Optional[str] = None
    misconception_tags: List[str] = Field(default_factory=list)


class ExaminationResultSummary(BaseModel):
    """Comprehensive performance report generated upon examination submission."""
    session_id: str
    student_id: str
    student_name: str
    paper_title: str
    paper_code: str
    blueprint_id: str
    status: ExaminationStatus
    total_marks: int
    score: float
    percentage: float
    duration_minutes: int
    time_spent_seconds: int
    is_timeout_submission: bool
    section_scores: Dict[str, Dict[str, Any]]
    unit_scores: Dict[str, Dict[str, Any]]
    chapter_scores: Dict[str, Dict[str, Any]]
    difficulty_scores: Dict[str, Dict[str, Any]]
    cognitive_scores: Dict[str, Dict[str, Any]]
    strong_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    weak_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    detected_misconceptions: List[str] = Field(default_factory=list)
    recommended_next_action: Dict[str, Any] = Field(default_factory=dict)
    question_reviews: List[ExamQuestionReviewItem] = Field(default_factory=list)
    started_at: str
    completed_at: str


class ExaminationOverviewItem(BaseModel):
    """Brief metadata card for available or completed examinations."""
    session_id: Optional[str] = None
    blueprint_id: str
    paper_title: str
    paper_code: str
    total_marks: int
    duration_minutes: int
    question_count: int
    status: ExaminationStatus
    score: Optional[float] = None
    percentage: Optional[float] = None
    completed_at: Optional[str] = None
    is_active: bool = False
