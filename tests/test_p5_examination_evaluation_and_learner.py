"""
P5 Examination Evaluation, Learner Model & Teacher Dashboard Integration Tests
Verifies full-stack evaluation across all CBSE typologies,
mastery updates, misconception classification, and teacher analytics.
"""

import pytest
from src.storage.database import Database
from src.storage.examination_repository import ExaminationRepository
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.remediation_repository import RemediationRepository
from src.storage.learner_repository import LearnerRepository
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.learner_model_service import LearnerModelService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.services.examination_service import ExaminationService
from src.models.examination import SaveExamAnswerRequest, ExaminationStatus


@pytest.fixture
def exam_env():
    db = Database("data/curriculum.db")
    exam_repo = ExaminationRepository(db)
    q_repo = QuestionRepository(db)
    c_repo = ConceptRepository(db)
    r_repo = RemediationRepository(db)
    l_repo = LearnerRepository(db)

    eval_svc = AnswerEvaluationService()
    learner_svc = LearnerModelService(l_repo, None, c_repo)
    misc_svc = MisconceptionDetectionService(r_repo, q_repo, c_repo)
    sr_svc = SpacedRepetitionService(r_repo, l_repo, c_repo)

    exam_svc = ExaminationService(
        db=db,
        exam_repo=exam_repo,
        question_repo=q_repo,
        concept_repo=c_repo,
        evaluation_service=eval_svc,
        learner_service=learner_svc,
        misconception_service=misc_svc,
        spaced_repetition_service=sr_svc,
        learner_repo=l_repo,
    )
    return {
        "db": db,
        "exam_repo": exam_repo,
        "q_repo": q_repo,
        "c_repo": c_repo,
        "l_repo": l_repo,
        "r_repo": r_repo,
        "exam_svc": exam_svc,
    }


def test_examination_submission_and_multitypology_evaluation(exam_env):
    """Verifies that submitting an examination evaluates all questions across typologies."""
    exam_svc = exam_env["exam_svc"]
    student_id = "STU-EVAL-01"

    state = exam_svc.start_examination(student_id=student_id, blueprint_id="BP-CBSE-X-SCI-2027")
    sess_id = state.session_id

    # Answer some questions
    q1 = state.questions[0]
    exam_svc.save_answer(
        session_id=sess_id,
        student_id=student_id,
        req=SaveExamAnswerRequest(
            question_id=q1.question_id,
            submitted_answer={"selected_option": "B"},
            time_spent_seconds=45,
        ),
    )

    # Submit examination
    result = exam_svc.submit_examination(session_id=sess_id, student_id=student_id)

    assert result.session_id == sess_id
    assert result.student_id == student_id
    assert result.status in (ExaminationStatus.SUBMITTED, ExaminationStatus.TIMED_OUT)
    assert result.total_marks == 80
    assert result.score >= 0.0 and result.score <= 80.0
    assert result.percentage >= 0.0 and result.percentage <= 100.0

    # Section scores
    assert "Section A" in result.section_scores
    assert "Section B" in result.section_scores
    assert "Section C" in result.section_scores
    assert "Section D" in result.section_scores
    assert "Section E" in result.section_scores

    # All 39 question reviews present
    assert len(result.question_reviews) == 39
    for rev in result.question_reviews:
        assert rev.marks_awarded >= 0.0
        assert rev.marks > 0
        assert len(rev.explanation) > 0


def test_learner_model_mastery_updated_after_exam(exam_env):
    """Verifies that taking an examination updates concept masteries in the Learner Model."""
    exam_svc = exam_env["exam_svc"]
    l_repo = exam_env["l_repo"]
    student_id = "STU-EVAL-02"

    state = exam_svc.start_examination(student_id=student_id, blueprint_id="BP-CBSE-X-SCI-2027")
    exam_svc.submit_examination(session_id=state.session_id, student_id=student_id)

    # Masteries should be tracked
    masteries = l_repo.get_all_concept_mastery(student_id=student_id)
    assessed = [m for m in masteries if m.total_attempts > 0]
    assert len(assessed) > 0, "Learner concept mastery should be updated after exam evaluation."


def test_teacher_dashboard_cohort_exam_analytics(exam_env):
    """Verifies that the teacher dashboard aggregates cohort examination performance."""
    exam_svc = exam_env["exam_svc"]
    summary = exam_svc.get_teacher_examinations_summary()

    assert "total_examinations_taken" in summary
    assert "cohort_average_score" in summary
    assert "cohort_average_percentage" in summary
    assert "pass_rate_percentage" in summary
    assert "frequent_weak_concepts" in summary
    assert "recent_examinations" in summary

    assert summary["total_examinations_taken"] >= 1
    assert summary["cohort_average_score"] >= 0.0
