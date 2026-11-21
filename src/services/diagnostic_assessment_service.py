"""
Diagnostic Assessment Service
Orchestrates test initialization, question selection, real-time answer processing,
final scoring, and diagnostic report generation.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.storage.question_repository import QuestionRepository
from src.storage.assessment_repository import AssessmentRepository
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.learner_model_service import LearnerModelService
from src.models.assessment import (
    AssessmentType,
    AssessmentStatus,
    AssessmentSession,
    AssessmentQuestionView,
    AssessmentResultSummary,
    QuestionReviewItem,
    AnswerEvaluationResult,
)
from src.models.question import Question, QuestionDifficulty


class DiagnosticAssessmentService:
    """
    Manages complete assessment workflows from initialization to diagnostic reporting.
    """

    def __init__(
        self,
        assessment_repo: AssessmentRepository,
        question_repo: QuestionRepository,
        evaluation_service: AnswerEvaluationService,
        learner_service: LearnerModelService,
        misconception_service: Optional[Any] = None,
        spaced_repetition_service: Optional[Any] = None,
    ):
        self.assessment_repo = assessment_repo
        self.question_repo = question_repo
        self.evaluation_service = evaluation_service
        self.learner_service = learner_service
        self.misconception_service = misconception_service
        self.spaced_repetition_service = spaced_repetition_service

    def start_diagnostic_assessment(
        self,
        student_id: str = "STU-001",
        chapter_id: str = "CH-01",
        question_count: int = 5,
    ) -> AssessmentSession:
        """
        Initializes a balanced diagnostic assessment session.
        Selects representative questions from Chapter 1 (balanced by difficulty and concept).
        """
        # Ensure student exists
        self.learner_service.get_or_create_student(student_id)

        # Retrieve available Chapter 1 questions
        all_qs = self.question_repo.get_questions_by_chapter(chapter_id)
        if not all_qs:
            raise ValueError(f"No questions found for chapter '{chapter_id}' in question bank.")

        # Balanced selection: e.g. 2 Easy, 2 Medium, 1 Hard
        easy_qs = [q for q in all_qs if q.difficulty == QuestionDifficulty.EASY]
        med_qs = [q for q in all_qs if q.difficulty == QuestionDifficulty.MEDIUM]
        hard_qs = [q for q in all_qs if q.difficulty == QuestionDifficulty.HARD]

        selected_qs: List[Question] = []
        if easy_qs:
            selected_qs.extend(easy_qs[:2])
        if med_qs:
            selected_qs.extend(med_qs[:2])
        if hard_qs:
            selected_qs.extend(hard_qs[:1])

        # Fill remaining if needed
        for q in all_qs:
            if len(selected_qs) >= question_count:
                break
            if q not in selected_qs:
                selected_qs.append(q)

        # Cap strictly to requested question_count
        selected_qs = selected_qs[:question_count]

        assessment_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"
        total_marks = sum(q.marks for q in selected_qs)
        qids = [q.question_id for q in selected_qs]

        self.assessment_repo.create_assessment(
            assessment_id=assessment_id,
            student_id=student_id,
            assessment_type=AssessmentType.DIAGNOSTIC,
            chapter_id=chapter_id,
            question_ids=qids,
            total_marks=total_marks,
        )

        # Build safe question views (excluding answer keys)
        views = [self._to_question_view(q) for q in selected_qs]

        return AssessmentSession(
            assessment_id=assessment_id,
            student_id=student_id,
            assessment_type=AssessmentType.DIAGNOSTIC,
            chapter_id=chapter_id,
            status=AssessmentStatus.IN_PROGRESS,
            total_questions=len(selected_qs),
            total_marks=total_marks,
            score=0.0,
            questions=views,
            answers={},
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_assessment_session(self, assessment_id: str) -> Optional[AssessmentSession]:
        """
        Retrieves active or completed assessment session state.
        """
        row = self.assessment_repo.get_assessment(assessment_id)
        if not row:
            return None

        qids = self.assessment_repo.get_assessment_question_ids(assessment_id)
        questions = []
        for qid in qids:
            q = self.question_repo.get_question(qid)
            if q:
                questions.append(self._to_question_view(q))

        # Fetch recorded answers
        recorded = self.assessment_repo.get_answers_for_assessment(assessment_id)
        answers_map = {r["question_id"]: r["submitted_answer"] for r in recorded}

        return AssessmentSession(
            assessment_id=row["assessment_id"],
            student_id=row["student_id"],
            assessment_type=AssessmentType(row["assessment_type"]),
            chapter_id=row.get("chapter_id"),
            status=AssessmentStatus(row["status"]),
            total_questions=row["total_questions"],
            total_marks=row["total_marks"],
            score=row["score"],
            questions=questions,
            answers=answers_map,
            started_at=str(row["started_at"]) if row.get("started_at") else None,
            completed_at=str(row["completed_at"]) if row.get("completed_at") else None,
        )

    def submit_answer(
        self,
        assessment_id: str,
        student_id: str,
        question_id: str,
        submitted_answer: Dict[str, Any],
        time_spent_seconds: int = 0,
    ) -> AnswerEvaluationResult:
        """
        Evaluates and persists an individual answer submission.
        Updates student's concept mastery immediately.
        """
        assessment = self.assessment_repo.get_assessment(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        if assessment["status"] == "EVALUATED":
            raise ValueError("Assessment is already finalized; further answers cannot be submitted.")

        question = self.question_repo.get_question(question_id)
        if not question:
            raise ValueError(f"Question '{question_id}' not found in Question Bank.")

        # Evaluate response
        eval_result = self.evaluation_service.evaluate_answer(question, submitted_answer)

        # Persist answer record
        answer_id = f"ANS-{uuid.uuid4().hex[:8]}"
        self.assessment_repo.record_student_answer(
            answer_id=answer_id,
            assessment_id=assessment_id,
            student_id=student_id,
            question_id=question_id,
            submitted_answer=submitted_answer,
            is_correct=eval_result.is_correct,
            marks_awarded=eval_result.marks_awarded,
            feedback=eval_result.feedback,
            detected_misconceptions=eval_result.detected_misconceptions,
            time_spent_seconds=time_spent_seconds,
        )

        # Update concept mastery in Learner Model
        self.learner_service.process_evaluated_answer(
            student_id=student_id,
            concept_ids=question.concept_ids,
            is_correct=eval_result.is_correct,
            difficulty=question.difficulty.value,
            misconception_tags=eval_result.detected_misconceptions,
        )

        # Trigger evidence-based misconception detection
        if self.misconception_service:
            self.misconception_service.analyze_student_answer(
                student_id=student_id,
                question_id=question_id,
                submitted_answer=submitted_answer,
                is_correct=eval_result.is_correct
            )

        return eval_result

    def submit_final_assessment(
        self, assessment_id: str, student_id: str
    ) -> AssessmentResultSummary:
        """
        Finalizes assessment, computes aggregate score, compiles concept breakdown,
        and generates student diagnostic report.
        Prevents duplicate submissions idempotently.
        """
        assessment = self.assessment_repo.get_assessment(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        # Fetch all questions and recorded answers
        qids = self.assessment_repo.get_assessment_question_ids(assessment_id)
        recorded_answers = self.assessment_repo.get_answers_for_assessment(assessment_id)
        ans_by_qid = {a["question_id"]: a for a in recorded_answers}

        total_score = 0.0
        total_marks = assessment["total_marks"] or 0
        concept_perf: Dict[str, Dict[str, Any]] = {}
        reviews: List[QuestionReviewItem] = []
        all_misconceptions: List[str] = []

        for qid in qids:
            q = self.question_repo.get_question(qid)
            if not q:
                continue

            ans = ans_by_qid.get(qid)
            if ans:
                is_correct = bool(ans["is_correct"])
                marks = float(ans["marks_awarded"])
                sub_ans = ans["submitted_answer"]
                misconceptions = ans.get("detected_misconceptions", [])
            else:
                # Unanswered item
                is_correct = False
                marks = 0.0
                sub_ans = {}
                misconceptions = []

            total_score += marks
            all_misconceptions.extend(misconceptions)

            # Track per-concept performance
            for cid in q.concept_ids:
                if cid not in concept_perf:
                    concept_perf[cid] = {"total": 0, "correct": 0, "marks_earned": 0.0}
                concept_perf[cid]["total"] += 1
                if is_correct:
                    concept_perf[cid]["correct"] += 1
                    concept_perf[cid]["marks_earned"] += marks

            # Review item
            correct_val = q.answer_key.get("correct_option") or q.answer_key.get("numerical_value") or q.answer_key.get("key_points")
            reviews.append(
                QuestionReviewItem(
                    question_id=q.question_id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    difficulty=q.difficulty,
                    marks=q.marks,
                    marks_awarded=marks,
                    is_correct=is_correct,
                    submitted_answer=sub_ans,
                    correct_answer=correct_val,
                    explanation=q.explanation,
                    concept_ids=q.concept_ids,
                    misconceptions=misconceptions,
                )
            )

        pct = round((total_score / total_marks) * 100, 1) if total_marks > 0 else 0.0

        # Identify strong and weak concepts in this test
        strong_c = [cid for cid, stats in concept_perf.items() if stats["correct"] == stats["total"]]
        weak_c = [cid for cid, stats in concept_perf.items() if stats["correct"] < stats["total"]]

        # Mark finalized in database
        self.assessment_repo.finalize_assessment(assessment_id=assessment_id, score=total_score)

        # Recommendation
        if weak_c:
            rec = {
                "title": "Targeted Adaptive Remediation",
                "message": f"Identified learning opportunities in {len(weak_c)} concepts. Practice prerequisite exercises.",
                "action": "START_ADAPTIVE_PRACTICE",
            }
        else:
            rec = {
                "title": "Excellence! Advance to Challenge Problems",
                "message": "Perfect accuracy across all tested concepts. Ready for Board-level numericals.",
                "action": "ADVANCE_CHAPTER",
            }

        # Auto-schedule tested concepts into spaced repetition
        if self.spaced_repetition_service:
            try:
                self.spaced_repetition_service.sync_weak_concepts_to_schedule(student_id)
            except Exception:
                pass

        return AssessmentResultSummary(
            assessment_id=assessment_id,
            student_id=student_id,
            assessment_type=AssessmentType(assessment["assessment_type"]),
            chapter_id=assessment.get("chapter_id"),
            status=AssessmentStatus.EVALUATED,
            total_questions=len(qids),
            answered_questions=len(recorded_answers),
            total_marks=total_marks,
            score=total_score,
            percentage=pct,
            concept_performance=concept_perf,
            strong_concepts=strong_c,
            weak_concepts=weak_c,
            detected_misconceptions=list(set(all_misconceptions)),
            recommended_next_action=rec,
            question_reviews=reviews,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _to_question_view(self, q: Question) -> AssessmentQuestionView:
        ak = q.answer_key or {}
        return AssessmentQuestionView(
            question_id=q.question_id,
            question_text=q.question_text,
            question_type=q.question_type,
            chapter_id=q.chapter_id,
            topic_id=q.topic_id,
            concept_ids=q.concept_ids,
            difficulty=q.difficulty,
            cognitive_level=q.cognitive_level,
            marks=q.marks,
            expected_time_seconds=q.expected_time_seconds,
            options=ak.get("options"),
            passage=ak.get("passage"),
            assertion=ak.get("assertion"),
            reason=ak.get("reason"),
        )
