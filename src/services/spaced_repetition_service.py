"""
Spaced Repetition Service
Implements deterministic, mastery-guided revision intervals: 1d -> 3d -> 7d -> 14d -> 30d.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.storage.remediation_repository import RemediationRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.models.spaced_repetition import (
    ReviewStatus,
    SpacedRepetitionItem,
    CompleteRevisionResponse,
)


class SpacedRepetitionService:
    INTERVAL_LADDER = [1, 3, 7, 14, 30, 60]

    def __init__(
        self,
        remediation_repo: RemediationRepository,
        learner_repo: LearnerRepository,
        concept_repo: ConceptRepository
    ):
        self.remediation_repo = remediation_repo
        self.learner_repo = learner_repo
        self.concept_repo = concept_repo

    def schedule_concept_review(
        self,
        student_id: str,
        concept_id: str,
        initial_interval_days: int = 1,
        initial_mastery: float = 0.0
    ) -> SpacedRepetitionItem:
        """Schedules a new or reset review for a concept."""
        return self.remediation_repo.schedule_or_update_revision(
            student_id=student_id,
            concept_id=concept_id,
            interval_days=initial_interval_days,
            ease_factor=2.5,
            last_result="NOT_REVIEWED",
            current_mastery=initial_mastery
        )

    def complete_revision(
        self,
        student_id: str,
        concept_id: str,
        is_correct: bool,
        difficulty_rating: str = "NORMAL"
    ) -> CompleteRevisionResponse:
        """
        Processes a completed revision check.
        Adjusts interval and mastery according to deterministic Leitner/SM-2 rules.
        """
        # Retrieve existing schedule
        schedules = self.remediation_repo.get_revision_schedules(student_id)
        current_item = next((s for s in schedules if s.concept_id == concept_id), None)

        current_interval = current_item.interval_days if current_item else 1
        current_ease = current_item.ease_factor if current_item else 2.5
        current_mastery = current_item.current_mastery if current_item else 0.5

        # Get latest mastery from learner repository if available
        mastery_item = self.learner_repo.get_concept_mastery(student_id, concept_id)
        if mastery_item:
            current_mastery = mastery_item.mastery_score

        if is_correct:
            # Advance to next interval on ladder
            try:
                curr_idx = self.INTERVAL_LADDER.index(current_interval)
                new_interval = self.INTERVAL_LADDER[min(curr_idx + 1, len(self.INTERVAL_LADDER) - 1)]
            except ValueError:
                # If interval was custom, scale by ease
                new_interval = max(3, int(current_interval * current_ease))

            # Modify ease factor
            if difficulty_rating == "EASY":
                new_ease = min(3.0, current_ease + 0.15)
                new_interval = int(new_interval * 1.2)
            elif difficulty_rating == "HARD":
                new_ease = max(1.3, current_ease - 0.15)
            else:
                new_ease = current_ease

            new_mastery = min(1.0, current_mastery + 0.10)
            result_str = "CORRECT"
            msg = f"Great work! Mastery increased to {int(new_mastery * 100)}%. Next review in {new_interval} days."
        else:
            # Fall back to 1 day on failure
            new_interval = 1
            new_ease = max(1.3, current_ease - 0.20)
            new_mastery = max(0.0, current_mastery - 0.15)
            result_str = "INCORRECT"
            msg = f"Concept needs reinforcement. Review interval reset to 1 day. Current mastery: {int(new_mastery * 100)}%."

        # Update mastery in learner ledger as well
        self.learner_repo.update_mastery(
            student_id=student_id,
            concept_id=concept_id,
            is_correct=is_correct,
            difficulty_multiplier=1.0
        )

        updated_sched = self.remediation_repo.schedule_or_update_revision(
            student_id=student_id,
            concept_id=concept_id,
            interval_days=new_interval,
            ease_factor=new_ease,
            last_result=result_str,
            current_mastery=new_mastery
        )

        return CompleteRevisionResponse(
            schedule_id=updated_sched.schedule_id,
            concept_id=concept_id,
            concept_name=updated_sched.concept_name,
            previous_interval_days=current_interval,
            new_interval_days=new_interval,
            next_review_at=updated_sched.next_review_at,
            new_mastery=new_mastery,
            message=msg
        )

    def get_due_revisions(self, student_id: str) -> List[SpacedRepetitionItem]:
        all_items = self.remediation_repo.get_revision_schedules(student_id)
        return [item for item in all_items if item.review_status in (ReviewStatus.DUE, ReviewStatus.OVERDUE)]

    def get_upcoming_revisions(self, student_id: str) -> List[SpacedRepetitionItem]:
        all_items = self.remediation_repo.get_revision_schedules(student_id)
        return [item for item in all_items if item.review_status == ReviewStatus.PENDING]

    def sync_weak_concepts_to_schedule(self, student_id: str):
        """Ensures that any concept where the student has taken an assessment is scheduled for spaced repetition."""
        mastery_items = self.learner_repo.get_all_concept_mastery(student_id)
        existing_schedules = {s.concept_id: s for s in self.remediation_repo.get_revision_schedules(student_id)}

        for m in mastery_items:
            if m.total_attempts > 0 and m.concept_id not in existing_schedules:
                # Initial interval based on performance: 1 day if developing, 3 days if strong
                init_interval = 3 if m.mastery_score >= 0.80 else 1
                self.schedule_concept_review(
                    student_id=student_id,
                    concept_id=m.concept_id,
                    initial_interval_days=init_interval,
                    initial_mastery=m.mastery_score
                )
