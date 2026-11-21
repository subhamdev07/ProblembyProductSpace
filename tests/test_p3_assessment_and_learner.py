"""
Unit Tests for P3 — Diagnostic Assessment and Learner Model Services
Tests answer evaluation (MCQ, Assertion-Reason, Numerical, Short Answer),
session management, Bayesian mastery updates, prerequisite traversal, and misconception tracking.
"""

import pytest
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.diagnostic_assessment_service import DiagnosticAssessmentService
from src.services.learner_model_service import LearnerModelService
from src.services.adaptive_selection_service import AdaptiveQuestionSelectionService

from src.storage.assessment_repository import AssessmentRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository

from src.models.question import Question, QuestionType, QuestionDifficulty, CognitiveLevel
from src.models.assessment import AssessmentType, AssessmentStatus
from src.models.learner import ConceptMasteryStatus


@pytest.fixture
def eval_service():
    return AnswerEvaluationService()


@pytest.fixture
def p3_repos(seeded_question_bank, seeded_concept_repo):
    """Provides wired repositories with curriculum, concept graph, and Chapter 1 questions."""
    db = seeded_question_bank.db
    q_repo = seeded_question_bank
    c_repo = seeded_concept_repo
    a_repo = AssessmentRepository(db)
    l_repo = LearnerRepository(db)
    return {
        "db": db,
        "question_repo": q_repo,
        "concept_repo": c_repo,
        "assessment_repo": a_repo,
        "learner_repo": l_repo,
    }


def test_mcq_evaluation(eval_service):
    """Test MCQ answer evaluation logic."""
    q = Question(
        question_id="Q-TEST-MCQ",
        question_text="Which gas is evolved?",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        marks=1,
        answer_key={"options": {"A": "O2", "B": "H2", "C": "N2", "D": "CO2"}, "correct_option": "B"},
        explanation="Hydrogen gas is evolved.",
    )

    # Correct
    res_correct = eval_service.evaluate_answer(q, {"selected_option": "B"})
    assert res_correct.is_correct is True
    assert res_correct.marks_awarded == 1.0
    assert "Correct!" in res_correct.feedback

    # Incorrect
    res_wrong = eval_service.evaluate_answer(q, {"selected_option": "A"})
    assert res_wrong.is_correct is False
    assert res_wrong.marks_awarded == 0.0
    assert "Incorrect" in res_wrong.feedback


def test_assertion_reason_evaluation(eval_service):
    """Test Assertion-Reason evaluation."""
    q = Question(
        question_id="Q-TEST-AR",
        question_text="Assertion and reason...",
        question_type=QuestionType.ASSERTION_REASON,
        chapter_id="CH-01",
        topic_id="CH01-T03",
        marks=1,
        answer_key={"assertion": "A", "reason": "R", "correct_option": "A"},
        explanation="Both true and R explains A.",
    )

    res = eval_service.evaluate_answer(q, {"selected_option": "A"})
    assert res.is_correct is True
    assert res.marks_awarded == 1.0


def test_numerical_evaluation(eval_service):
    """Test numerical evaluation with tolerance."""
    q = Question(
        question_id="Q-TEST-NUM",
        question_text="Calculate mass in grams:",
        question_type=QuestionType.NUMERICAL,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        marks=2,
        answer_key={"numerical_value": 44.0, "tolerance": 0.5, "unit": "g"},
        explanation="44 g of CO2.",
    )

    # Exact value
    res_exact = eval_service.evaluate_answer(q, {"numerical_value": 44.0})
    assert res_exact.is_correct is True
    assert res_exact.marks_awarded == 2.0

    # Within tolerance
    res_tol = eval_service.evaluate_answer(q, {"numerical_value": 44.3})
    assert res_tol.is_correct is True
    assert res_tol.marks_awarded == 2.0

    # Outside tolerance
    res_out = eval_service.evaluate_answer(q, {"numerical_value": 45.5})
    assert res_out.is_correct is False
    assert res_out.marks_awarded == 0.0


def test_short_answer_rubric_evaluation(eval_service):
    """Test Short Answer evaluation via rubric key_points."""
    q = Question(
        question_id="Q-TEST-SA",
        question_text="Why apply paint on iron articles?",
        question_type=QuestionType.SHORT_ANSWER,
        chapter_id="CH-01",
        topic_id="CH01-T03",
        marks=2,
        answer_key={
            "key_points": [
                "Paint forms a protective barrier.",
                "Prevents contact with moisture and oxygen.",
            ]
        },
        explanation="Paint blocks contact with air and moisture.",
    )

    # Student answer matching key points
    res = eval_service.evaluate_answer(
        q, {"text_answer": "Paint acts as a protective barrier preventing direct contact with oxygen and moisture."}
    )
    assert res.is_correct is True
    assert res.marks_awarded > 0.0


def test_diagnostic_assessment_flow(p3_repos, eval_service):
    """Test complete diagnostic session creation, answer recording, and final scoring."""
    a_repo = p3_repos["assessment_repo"]
    q_repo = p3_repos["question_repo"]
    l_repo = p3_repos["learner_repo"]
    c_repo = p3_repos["concept_repo"]

    l_service = LearnerModelService(l_repo, a_repo, c_repo)
    diag_service = DiagnosticAssessmentService(a_repo, q_repo, eval_service, l_service)

    # 1. Start assessment
    session = diag_service.start_diagnostic_assessment(
        student_id="STU-001", chapter_id="CH-01", question_count=5
    )
    assert session.assessment_id.startswith("ASM-")
    assert len(session.questions) == 5
    assert session.status == AssessmentStatus.IN_PROGRESS

    # 2. Submit answers for first 2 questions
    q1 = session.questions[0]
    # Q1 is Q-CH01-EAS-001 (correct option is C)
    res1 = diag_service.submit_answer(
        assessment_id=session.assessment_id,
        student_id="STU-001",
        question_id=q1.question_id,
        submitted_answer={"selected_option": "C"},
        time_spent_seconds=25,
    )
    assert res1.is_correct is True
    assert res1.marks_awarded == 1.0

    q2 = session.questions[1]
    # Q2 is Q-CH01-EAS-002 (correct option is B)
    res2 = diag_service.submit_answer(
        assessment_id=session.assessment_id,
        student_id="STU-001",
        question_id=q2.question_id,
        submitted_answer={"selected_option": "A"},  # intentionally wrong
        time_spent_seconds=30,
    )
    assert res2.is_correct is False
    assert res2.marks_awarded == 0.0

    # 3. Finalize assessment
    summary = diag_service.submit_final_assessment(
        assessment_id=session.assessment_id, student_id="STU-001"
    )
    assert summary.status == AssessmentStatus.EVALUATED
    assert summary.score >= 1.0
    assert len(summary.question_reviews) == 5
    assert summary.answered_questions == 2

    # 4. Attempting to submit another answer to an evaluated test should raise ValueError
    with pytest.raises(ValueError) as exc:
        diag_service.submit_answer(
            assessment_id=session.assessment_id,
            student_id="STU-001",
            question_id=q1.question_id,
            submitted_answer={"selected_option": "C"},
        )
    assert "already finalized" in str(exc.value)


def test_learner_mastery_and_adaptive_selection(p3_repos):
    """Test mastery updates and prerequisite graph traversal in adaptive selection."""
    l_repo = p3_repos["learner_repo"]
    q_repo = p3_repos["question_repo"]
    c_repo = p3_repos["concept_repo"]

    # Student fails concept CPT-CH01-020 (Displacement Reaction)
    l_repo.update_mastery(
        student_id="STU-TEST-001",
        concept_id="CPT-CH01-020",
        is_correct=False,
    )

    mastery = l_repo.get_concept_mastery("STU-TEST-001", "CPT-CH01-020")
    assert mastery is not None
    assert mastery.status == ConceptMasteryStatus.DEVELOPING
    assert mastery.mastery_score < 0.5

    # Adaptive question selection should target this weak concept or its prerequisite
    adaptive_service = AdaptiveQuestionSelectionService(q_repo, l_repo, c_repo)
    rec = adaptive_service.select_next_question(
        student_id="STU-TEST-001", chapter_id="CH-01"
    )

    assert rec.question is not None
    assert rec.target_concept_id in ("CPT-CH01-019", "CPT-CH01-020", "CPT-CH01-001", "CPT-CH01-003", "CPT-CH01-010")
    assert len(rec.selection_rationale) > 10
