"""
Learner Model Domain Entities
Defines concept mastery states, student profile, dashboard summary,
and adaptive recommendations.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ConceptMasteryStatus(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    DEVELOPING = "DEVELOPING"
    IMPROVING = "IMPROVING"
    STRONG = "STRONG"


class ConceptMasteryItem(BaseModel):
    """Detailed learner mastery state for a single concept node."""
    concept_id: str
    concept_name: str
    canonical_name: Optional[str] = None
    chapter_id: str
    topic_id: str
    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    status: ConceptMasteryStatus = ConceptMasteryStatus.NOT_ASSESSED
    total_attempts: int = 0
    correct_attempts: int = 0
    incorrect_attempts: int = 0
    last_attempted_at: Optional[str] = None


class StudentProfile(BaseModel):
    """Student profile metadata."""
    student_id: str
    name: str
    grade: int = 10
    created_at: Optional[str] = None


class StudentDashboardData(BaseModel):
    """Aggregated dashboard payload consumed by the frontend."""
    student: StudentProfile
    overall_mastery_pct: float
    total_assessments_taken: int
    total_questions_attempted: int
    overall_accuracy_pct: float
    mastery_distribution: Dict[str, int] = Field(default_factory=dict)
    strong_concepts: List[ConceptMasteryItem] = Field(default_factory=list)
    weak_concepts: List[ConceptMasteryItem] = Field(default_factory=list)
    recent_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    revision_due_concepts: List[ConceptMasteryItem] = Field(default_factory=list)
    recommended_action: Dict[str, Any] = Field(default_factory=dict)


class AdaptiveQuestionRecommendation(BaseModel):
    """Next best question tailored to the learner's diagnostic state."""
    question: Any
    target_concept_id: str
    target_concept_name: str
    selection_rationale: str
    difficulty: str
