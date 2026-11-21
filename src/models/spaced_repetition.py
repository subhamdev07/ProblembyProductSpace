"""
Spaced Repetition Domain Entities
Implements deterministic, mastery-based revision scheduling.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    DUE = "DUE"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class SpacedRepetitionItem(BaseModel):
    """A scheduled revision item for a specific curriculum concept."""
    schedule_id: str
    student_id: str
    concept_id: str
    concept_name: str
    chapter_id: str = "CH01"
    last_reviewed_at: Optional[str] = None
    next_review_at: str
    interval_days: int = 1
    ease_factor: float = 2.5
    review_count: int = 0
    last_result: Optional[str] = None
    current_mastery: float = 0.0
    review_status: ReviewStatus = ReviewStatus.PENDING
    days_until_due: int = 0


class CompleteRevisionRequest(BaseModel):
    """Request payload when a learner completes a concept review session."""
    student_id: str
    concept_id: str
    is_correct: bool
    difficulty_rating: Optional[str] = "NORMAL"  # EASY, NORMAL, HARD


class CompleteRevisionResponse(BaseModel):
    """Confirmation and new scheduling parameters after review."""
    schedule_id: str
    concept_id: str
    concept_name: str
    previous_interval_days: int
    new_interval_days: int
    next_review_at: str
    new_mastery: float
    message: str
