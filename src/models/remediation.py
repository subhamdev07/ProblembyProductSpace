"""
Remediation and Misconception Domain Entities
CBSE Class 10 Science (2026-27)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MisconceptionStatus(str, Enum):
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"


class StudentMisconceptionItem(BaseModel):
    misconception_record_id: str
    student_id: str
    concept_id: str
    concept_name: Optional[str] = None
    chapter_id: Optional[str] = "CH01"
    misconception_tag: str
    status: MisconceptionStatus = MisconceptionStatus.SUSPECTED
    evidence_count: int = 1
    evidence_text: Optional[str] = None
    parsed_evidences: Optional[List[Dict[str, Any]]] = None
    last_observed_at: Optional[str] = None


class TargetedRemediationPayload(BaseModel):
    """Scaffolded remediation package delivered when a learner exhibits difficulty."""
    remediation_id: str
    student_id: str
    concept_id: str
    concept_name: str
    prerequisite_concept_id: Optional[str] = None
    prerequisite_concept_name: Optional[str] = None
    gap_summary: str
    ncert_reference: str
    explanation: str
    example_activity: str
    practice_question: Optional[Dict[str, Any]] = None
    current_mastery: float = 0.0


class CompleteRemediationRequest(BaseModel):
    """Student submission for a targeted remediation practice question."""
    remediation_id: str
    student_id: str
    question_id: str
    student_answer: Any


class CompleteRemediationResponse(BaseModel):
    """Result of attempting a remediation practice item."""
    remediation_id: str
    concept_id: str
    is_correct: bool
    marks_awarded: float
    feedback: str
    mastery_before: float
    mastery_after: float
    mastery_delta: float
    next_revision_date: Optional[str] = None
