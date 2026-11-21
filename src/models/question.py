"""
Question Domain Models
Defines Question, QuestionType, QuestionDifficulty, CognitiveLevel,
QuestionStatus, and structured answer keys for P2 — Question Bank & Generation.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator

from src.models.concept import ConceptVerificationStatus, SourceStatus


class QuestionType(str, Enum):
    """
    Standard CBSE Class 10 Science question formats.
    """
    MCQ = "MCQ"
    SHORT_ANSWER = "SHORT_ANSWER"
    LONG_ANSWER = "LONG_ANSWER"
    ASSERTION_REASON = "ASSERTION_REASON"
    CASE_BASED = "CASE_BASED"
    NUMERICAL = "NUMERICAL"
    DIAGRAM_BASED = "DIAGRAM_BASED"


class QuestionDifficulty(str, Enum):
    """
    Cognitive complexity rubric:
    - EASY: Recall, direct recognition, single-step definitions or formulas.
    - MEDIUM: Conceptual reasoning, 2-step application, reaction balancing, distractor analysis.
    - HARD: Multi-step synthesis, cross-concept inference, case analysis, quantitative stoichiometry.
    """
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class CognitiveLevel(str, Enum):
    """
    CBSE Assessment Taxonomy Blueprint:
    - KNOWLEDGE_UNDERSTANDING: Demonstrate knowledge & understanding (50% target).
    - APPLICATION: Application of knowledge & concepts (30% target).
    - ANALYZE_EVALUATE_CREATE: Formulate, analyze, evaluate, and create (20% target).
    """
    KNOWLEDGE_UNDERSTANDING = "KNOWLEDGE_UNDERSTANDING"
    APPLICATION = "APPLICATION"
    ANALYZE_EVALUATE_CREATE = "ANALYZE_EVALUATE_CREATE"


class QuestionStatus(str, Enum):
    """
    Quality and moderation status for question bank records.
    - DRAFT: Initial generation or raw entry.
    - PENDING_REVIEW: Synthesized question requiring expert review.
    - VALIDATED: Formally passed 12-point quality check and verified.
    - REJECTED: Flagged as incorrect, ambiguous, or out of syllabus.
    """
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class QuestionProvenance(BaseModel):
    """
    Source citation and pedagogical context grounding the question.
    """
    source_document_id: str = Field(..., description="Registered source document ID, e.g. 'NCERT_SCI_10_CH01'")
    source_filename: str = Field(..., description="Document filename, e.g. 'jesc101.pdf'")
    page_number: Optional[int] = Field(None, description="Exact 1-indexed page in textbook")
    section_heading: Optional[str] = Field(None, description="Section heading in source")
    verbatim_source_context: Optional[str] = Field(None, description="Excerpt from textbook grounding question")


class Question(BaseModel):
    """
    Core Question entity representing an assessment item in the question bank.
    """
    question_id: str = Field(..., description="Stable deterministic ID, e.g. 'Q-CH01-MCQ-001'")
    question_text: str = Field(..., description="Question stem (supports LaTeX math syntax)")
    question_type: QuestionType = Field(..., description="Question typology")
    chapter_id: str = Field(..., description="Parent chapter ID, e.g. 'CH-01'")
    topic_id: str = Field(..., description="Parent topic ID, e.g. 'CH01-T01'")
    concept_ids: List[str] = Field(default_factory=list, description="Associated P1 concept IDs")
    learning_outcome_ids: List[str] = Field(default_factory=list, description="Associated CBSE LO IDs")
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MEDIUM)
    cognitive_level: CognitiveLevel = Field(default=CognitiveLevel.KNOWLEDGE_UNDERSTANDING)
    marks: int = Field(default=1, ge=1, le=10, description="Marks allocated per CBSE pattern")
    expected_time_seconds: int = Field(default=60, ge=10, le=900, description="Estimated time for student response")
    answer_key: Dict[str, Any] = Field(..., description="Structured answer key schema")
    explanation: str = Field(..., description="Comprehensive step-by-step rationale for the solution")
    misconception_tags: List[str] = Field(default_factory=list, description="Common error / misconception tags")
    source_status: SourceStatus = Field(default=SourceStatus.SOURCE_DERIVED)
    verification_status: ConceptVerificationStatus = Field(default=ConceptVerificationStatus.VERIFIED)
    question_status: QuestionStatus = Field(default=QuestionStatus.VALIDATED)
    provenance: Optional[QuestionProvenance] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode="after")
    def validate_answer_key_structure(self):
        """
        Enforces answer key schema compliance according to question_type.
        """
        ak = self.answer_key
        if self.question_type == QuestionType.MCQ:
            if "options" not in ak or "correct_option" not in ak:
                raise ValueError("MCQ answer_key must contain 'options' dict and 'correct_option' string.")
            opts = ak["options"]
            correct = ak["correct_option"]
            if not isinstance(opts, dict) or len(opts) < 2:
                raise ValueError("MCQ options must be a dictionary with at least 2 choices (typically A, B, C, D).")
            if correct not in opts:
                raise ValueError(f"MCQ correct_option '{correct}' must be a key in options: {list(opts.keys())}")

        elif self.question_type == QuestionType.ASSERTION_REASON:
            if "correct_option" not in ak or "assertion" not in ak or "reason" not in ak:
                raise ValueError("ASSERTION_REASON answer_key must include 'assertion', 'reason', and 'correct_option'.")
            valid_ar_opts = {"A", "B", "C", "D"}
            if ak["correct_option"].upper() not in valid_ar_opts:
                raise ValueError(f"Assertion-Reason correct_option must be one of {valid_ar_opts}")

        elif self.question_type == QuestionType.NUMERICAL:
            if "numerical_value" not in ak:
                raise ValueError("NUMERICAL answer_key must contain 'numerical_value'.")

        elif self.question_type in (QuestionType.SHORT_ANSWER, QuestionType.LONG_ANSWER):
            if "key_points" not in ak and "acceptable_answers" not in ak:
                raise ValueError(f"{self.question_type} answer_key must contain 'key_points' or 'acceptable_answers'.")

        elif self.question_type == QuestionType.CASE_BASED:
            if "passage" not in ak or "sub_questions" not in ak:
                raise ValueError("CASE_BASED answer_key must contain 'passage' and 'sub_questions'.")

        return self
