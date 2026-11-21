"""
Adaptive Question Selection Service
Implements intelligent pedagogical question selection based on learner diagnostic state,
P1 Concept Graph prerequisite traversal, and difficulty scaffolding.
"""

from typing import Optional, List, Dict, Any

from src.storage.question_repository import QuestionRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.models.learner import AdaptiveQuestionRecommendation, ConceptMasteryStatus
from src.models.assessment import AssessmentQuestionView
from src.models.question import QuestionDifficulty


class AdaptiveQuestionSelectionService:
    """
    Selects optimal next learning questions based on graph prerequisites and learner mastery.
    """

    def __init__(
        self,
        question_repo: QuestionRepository,
        learner_repo: LearnerRepository,
        concept_repo: Optional[ConceptRepository] = None,
    ):
        self.question_repo = question_repo
        self.learner_repo = learner_repo
        self.concept_repo = concept_repo

    def select_next_question(
        self,
        student_id: str = "STU-001",
        chapter_id: str = "CH-01",
        exclude_question_ids: Optional[List[str]] = None,
    ) -> AdaptiveQuestionRecommendation:
        """
        Picks the optimal next assessment item tailored to the student's learning frontier.
        """
        exclude_set = set(exclude_question_ids or [])
        all_mastery = self.learner_repo.get_all_concept_mastery(student_id=student_id, chapter_id=chapter_id)

        # 1. Check for weak concepts (score < 0.5 and attempted)
        weak_concepts = [m for m in all_mastery if m.status == ConceptMasteryStatus.DEVELOPING]
        unassessed_concepts = [m for m in all_mastery if m.status == ConceptMasteryStatus.NOT_ASSESSED]
        improving_concepts = [m for m in all_mastery if m.status == ConceptMasteryStatus.IMPROVING]

        target_concept = None
        target_diff = QuestionDifficulty.MEDIUM
        rationale = ""

        if weak_concepts:
            # Sort by lowest mastery score
            weak_concepts.sort(key=lambda x: x.mastery_score)
            primary_weak = weak_concepts[0]

            # Prerequisite inspection: check if this weak concept has prerequisites that are also weak
            prereq_target = None
            if self.concept_repo:
                prereq_ids = self.concept_repo.get_direct_prerequisites(primary_weak.concept_id)
                for pr_id in prereq_ids:
                    pr_mastery = self.learner_repo.get_concept_mastery(student_id, pr_id)
                    if not pr_mastery or pr_mastery.mastery_score < 0.6:
                        pr_node = self.concept_repo.get_concept(pr_id)
                        if pr_node:
                            prereq_target = pr_node
                            break

            if prereq_target:
                target_concept = prereq_target.concept_id
                concept_name = prereq_target.name
                target_diff = QuestionDifficulty.EASY
                rationale = (
                    f"Selected foundational concept '{concept_name}' because it is a prerequisite for "
                    f"'{primary_weak.concept_name}' where you experienced difficulty."
                )
            else:
                target_concept = primary_weak.concept_id
                concept_name = primary_weak.concept_name
                target_diff = QuestionDifficulty.EASY if primary_weak.mastery_score < 0.3 else QuestionDifficulty.MEDIUM
                rationale = (
                    f"Targeting '{concept_name}' (Current mastery: {int(primary_weak.mastery_score * 100)}%) "
                    f"to reinforce understanding and remediate errors."
                )

        elif unassessed_concepts:
            # Pick first unassessed concept
            target_item = unassessed_concepts[0]
            target_concept = target_item.concept_id
            concept_name = target_item.concept_name
            target_diff = QuestionDifficulty.EASY
            rationale = f"Assessing '{concept_name}' for the first time to build comprehensive diagnostic baseline."

        elif improving_concepts:
            target_item = improving_concepts[0]
            target_concept = target_item.concept_id
            concept_name = target_item.concept_name
            target_diff = QuestionDifficulty.MEDIUM
            rationale = f"Reinforcing '{concept_name}' to push mastery into the STRONG tier."

        else:
            # All assessed and strong -> Challenge with HARD
            target_item = all_mastery[0] if all_mastery else None
            target_concept = target_item.concept_id if target_item else "CPT-CH01-001"
            concept_name = target_item.concept_name if target_item else "Chemical Equations"
            target_diff = QuestionDifficulty.HARD
            rationale = "High overall mastery detected! Selected an advanced synthesis question to test deep application."

        # Fetch candidate questions for the targeted concept
        candidates = self.question_repo.get_questions_by_concept(target_concept)
        available = [q for q in candidates if q.question_id not in exclude_set]

        # If available questions found matching target difficulty
        diff_matches = [q for q in available if q.difficulty == target_diff]
        selected_q = diff_matches[0] if diff_matches else (available[0] if available else None)

        # Fallback: if no candidates for this concept, pick any unattempted question in chapter
        if not selected_q:
            all_ch_qs = self.question_repo.get_questions_by_chapter(chapter_id)
            unattempted = [q for q in all_ch_qs if q.question_id not in exclude_set]
            if unattempted:
                selected_q = unattempted[0]
                concept_name = selected_q.concept_ids[0] if selected_q.concept_ids else "Chemical Reactions"
                rationale = f"Broad diagnostic item chosen to expand syllabus coverage."
            else:
                # If all attempted, wrap around to first question
                selected_q = all_ch_qs[0]
                rationale = "Revision item: reinforcing previously attempted core syllabus question."

        # Safe view for frontend
        ak = selected_q.answer_key or {}
        qview = AssessmentQuestionView(
            question_id=selected_q.question_id,
            question_text=selected_q.question_text,
            question_type=selected_q.question_type,
            chapter_id=selected_q.chapter_id,
            topic_id=selected_q.topic_id,
            concept_ids=selected_q.concept_ids,
            difficulty=selected_q.difficulty,
            cognitive_level=selected_q.cognitive_level,
            marks=selected_q.marks,
            expected_time_seconds=selected_q.expected_time_seconds,
            options=ak.get("options"),
            passage=ak.get("passage"),
            assertion=ak.get("assertion"),
            reason=ak.get("reason"),
        )

        return AdaptiveQuestionRecommendation(
            question=qview,
            target_concept_id=target_concept,
            target_concept_name=concept_name,
            selection_rationale=rationale,
            difficulty=selected_q.difficulty.value,
        )
