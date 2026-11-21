"""
Student Telemetry and Activity Tracking Models
Captures all student interactions across diagnostics, examinations,
remediations, and concept mastery.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RecordActivityRequest(BaseModel):
    student_id: str
    event_type: str = Field(..., description="E.g. AUTH_LOGIN, QUESTION_ATTEMPT, BOARD_EXAM_START, REMEDIATION_COMPLETE")
    action_title: str = Field(..., description="Human-readable title of the activity")
    details: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary structured metadata")
    duration_seconds: int = Field(0, description="Active time spent in seconds")


class StudentActivityLog(BaseModel):
    log_id: str
    student_id: str
    event_type: str
    action_title: str
    details: Dict[str, Any]
    duration_seconds: int
    created_at: str


class StudentTelemetrySummary(BaseModel):
    student_id: str
    student_name: str
    total_activities: int
    total_active_seconds: int
    total_study_minutes: float
    diagnostic_tests_count: int
    board_exams_count: int
    questions_attempted: int
    remediations_completed: int
    revisions_completed: int
    misconceptions_active: int
    misconceptions_resolved: int
    last_active_at: Optional[str] = None
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)
