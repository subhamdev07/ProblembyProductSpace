"""
Learner Model Service
Orchestrates concept mastery tracking, Bayesian confidence updates,
misconception aggregation, and dashboard statistics compilation.
"""

from typing import List, Dict, Any, Optional

from src.storage.learner_repository import LearnerRepository
from src.storage.assessment_repository import AssessmentRepository
from src.storage.concept_repository import ConceptRepository
from src.models.learner import (
    ConceptMasteryStatus,
    ConceptMasteryItem,
    StudentProfile,
    StudentDashboardData,
)


class LearnerModelService:
    """
    Business logic for learner profile management, mastery analytics, and diagnostic progress.
    """

    def __init__(
        self,
        learner_repo: LearnerRepository,
        assessment_repo: Optional[AssessmentRepository] = None,
        concept_repo: Optional[ConceptRepository] = None,
    ):
        self.learner_repo = learner_repo
        self.assessment_repo = assessment_repo
        self.concept_repo = concept_repo

    def get_or_create_student(self, student_id: str = "STU-001") -> StudentProfile:
        return self.learner_repo.get_or_create_student(student_id=student_id)

    def process_evaluated_answer(
        self,
        student_id: str,
        concept_ids: List[str],
        is_correct: bool,
        difficulty: str = "MEDIUM",
        misconception_tags: Optional[List[str]] = None,
    ) -> List[ConceptMasteryItem]:
        """
        Updates concept mastery scores across all concepts touched by an answer.
        Logs any detected misconceptions.
        """
        diff_weights = {"EASY": 0.8, "MEDIUM": 1.0, "HARD": 1.3}
        weight = diff_weights.get(difficulty.upper(), 1.0)

        updated_items = []
        for cid in concept_ids:
            item = self.learner_repo.update_mastery(
                student_id=student_id,
                concept_id=cid,
                is_correct=is_correct,
                difficulty_multiplier=weight,
            )
            if item:
                updated_items.append(item)

            if not is_correct and misconception_tags:
                self.learner_repo.record_misconceptions(
                    student_id=student_id,
                    concept_id=cid,
                    misconception_tags=misconception_tags,
                )

        return updated_items

    def get_student_dashboard(self, student_id: str = "STU-001") -> StudentDashboardData:
        """
        Compiles the full student dashboard payload.
        """
        student = self.learner_repo.get_or_create_student(student_id=student_id)
        all_mastery = self.learner_repo.get_all_concept_mastery(student_id=student_id, chapter_id="CH-01")

        # Distribution
        dist = {
            "STRONG": 0,
            "IMPROVING": 0,
            "DEVELOPING": 0,
            "NOT_ASSESSED": 0,
        }
        total_score_sum = 0.0
        assessed_count = 0
        total_attempts = 0
        total_correct = 0

        strong_list = []
        weak_list = []
        revision_list = []

        for m in all_mastery:
            dist[m.status.value] += 1
            total_attempts += m.total_attempts
            total_correct += m.correct_attempts

            if m.status != ConceptMasteryStatus.NOT_ASSESSED:
                total_score_sum += m.mastery_score
                assessed_count += 1

            if m.status == ConceptMasteryStatus.STRONG:
                strong_list.append(m)
            elif m.status == ConceptMasteryStatus.DEVELOPING:
                weak_list.append(m)
            elif m.status == ConceptMasteryStatus.IMPROVING:
                revision_list.append(m)

        overall_mastery_pct = round((total_score_sum / assessed_count) * 100, 1) if assessed_count > 0 else 0.0
        overall_accuracy_pct = round((total_correct / total_attempts) * 100, 1) if total_attempts > 0 else 0.0

        # Recent assessments
        recent_assessments = []
        if self.assessment_repo:
            recent_assessments = self.assessment_repo.get_student_assessment_history(student_id=student_id, limit=5)

        # Recommended next action
        if not recent_assessments:
            rec_action = {
                "title": "Start Diagnostic Assessment",
                "description": "Establish your baseline mastery across Chemical Reactions & Equations (Chapter 1).",
                "cta_label": "Start Diagnostic Test",
                "type": "START_DIAGNOSTIC",
            }
        elif weak_list:
            top_weak = weak_list[0]
            rec_action = {
                "title": f"Practice: {top_weak.concept_name}",
                "description": f"Mastery is currently at {int(top_weak.mastery_score * 100)}%. Target prerequisite review.",
                "cta_label": "Take Adaptive Practice",
                "type": "ADAPTIVE_PRACTICE",
                "concept_id": top_weak.concept_id,
            }
        else:
            rec_action = {
                "title": "Comprehensive Revision",
                "description": "Great progress! Strengthen your mastery with mixed-difficulty board exam challenges.",
                "cta_label": "Start Revision Quiz",
                "type": "REVISION",
            }

        return StudentDashboardData(
            student=student,
            overall_mastery_pct=overall_mastery_pct,
            total_assessments_taken=len(recent_assessments),
            total_questions_attempted=total_attempts,
            overall_accuracy_pct=overall_accuracy_pct,
            mastery_distribution=dist,
            strong_concepts=strong_list[:5],
            weak_concepts=weak_list[:5],
            recent_assessments=recent_assessments,
            revision_due_concepts=revision_list[:5],
            recommended_action=rec_action,
        )
