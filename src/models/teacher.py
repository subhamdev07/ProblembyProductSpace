from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.learner import StudentProfile, ConceptMasteryItem
from src.models.remediation import StudentMisconceptionItem
from src.models.spaced_repetition import SpacedRepetitionItem


class TeacherDashboardData(BaseModel):
    total_students: int
    total_assessments_completed: int
    average_accuracy_pct: float
    average_concept_mastery_pct: float
    weakest_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    common_misconceptions: List[Dict[str, Any]] = Field(default_factory=list)
    students_requiring_intervention: List[Dict[str, Any]] = Field(default_factory=list)
    students: List[Dict[str, Any]] = Field(default_factory=list)
    revision_completion_rate_pct: float = 0.0
    chapter_performance: List[Dict[str, Any]] = Field(default_factory=list)


class TeacherStudentDetail(BaseModel):
    student: StudentProfile
    mastery_distribution: Dict[str, int]
    overall_accuracy_pct: float
    assessment_history: List[Dict[str, Any]] = Field(default_factory=list)
    active_misconceptions: List[StudentMisconceptionItem] = Field(default_factory=list)
    weak_concepts: List[ConceptMasteryItem] = Field(default_factory=list)
    scheduled_revisions: List[SpacedRepetitionItem] = Field(default_factory=list)
    intervention_notes: List[str] = Field(default_factory=list)
