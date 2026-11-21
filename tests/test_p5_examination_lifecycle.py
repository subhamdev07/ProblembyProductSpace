"""
P5 Examination Session Lifecycle Tests
Tests starting, real-time persistence, browser refresh recovery,
and authoritative countdown timer behavior.
"""

import pytest
from datetime import datetime, timezone, timedelta
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
from src.models.examination import ExaminationStatus, SaveExamAnswerRequest


@pytest.fixture
def exam_service():
    db = Database("data/curriculum.db")
    exam_repo = ExaminationRepository(db)
    q_repo = QuestionRepository(db)
    c_repo = ConceptRepository(db)
    r_repo = RemediationRepository(db)
    l_repo = LearnerRepository(db)

    return ExaminationService(
        db=db,
        exam_repo=exam_repo,
        question_repo=q_repo,
        concept_repo=c_repo,
        evaluation_service=AnswerEvaluationService(),
        learner_service=LearnerModelService(l_repo, None, c_repo),
        misconception_service=MisconceptionDetectionService(r_repo, q_repo, c_repo),
        spaced_repetition_service=SpacedRepetitionService(r_repo, l_repo, c_repo),
    )


def test_start_examination_creates_authoritative_session(exam_service):
    """Verifies that starting an examination initializes the 39 questions, timer, and student view."""
    student_id = "STU-TEST-01"
    state = exam_service.start_examination(student_id=student_id, blueprint_id="BP-CBSE-X-SCI-2027")

    assert state.session_id.startswith("EXAM-")
    assert state.student_id == student_id
    assert state.status == ExaminationStatus.IN_PROGRESS
    assert state.total_questions == 39
    assert state.total_marks == 80
    assert state.duration_minutes == 180
    assert state.remaining_time_seconds > 0 and state.remaining_time_seconds <= 180 * 60

    # Ensure no answer keys or explanations are leaked
    for q in state.questions:
        assert hasattr(q, "question_text")
        # Check that internal fields are NOT present
        assert not hasattr(q, "answer_key")
        assert not hasattr(q, "explanation")


def test_real_time_answer_persistence_and_recovery(exam_service):
    """Verifies that saving an answer persists to the database and survives session reload."""
    student_id = "STU-TEST-02"
    state = exam_service.start_examination(student_id=student_id, blueprint_id="BP-CBSE-X-SCI-2027")
    sess_id = state.session_id

    q1 = state.questions[0]
    q2 = state.questions[1]

    # Save answer for Q1
    save_res = exam_service.save_answer(
        session_id=sess_id,
        student_id=student_id,
        req=SaveExamAnswerRequest(
            question_id=q1.question_id,
            submitted_answer={"selected_option": "B"},
            is_marked_for_review=True,
            time_spent_seconds=40,
        ),
    )

    assert save_res.is_saved is True
    assert save_res.is_marked_for_review is True
    assert save_res.answered_count == 1
    assert save_res.marked_count == 1

    # Reload session state (simulating browser refresh)
    recovered_state = exam_service.get_session_state(session_id=sess_id, student_id=student_id)
    assert recovered_state.answered_count == 1
    assert q1.question_id in recovered_state.saved_answers
    assert recovered_state.saved_answers[q1.question_id]["selected_option"] == "B"
    assert q1.question_id in recovered_state.marked_for_review


def test_active_session_retrieval(exam_service):
    """Verifies that a student's active in-progress examination is detected."""
    student_id = "STU-TEST-03"
    state = exam_service.start_examination(student_id=student_id, blueprint_id="BP-CBSE-X-SCI-2027")

    active = exam_service.exam_repo.get_active_session_for_student(student_id)
    assert active is not None
    assert active["session_id"] == state.session_id
    assert active["status"] == "IN_PROGRESS"
