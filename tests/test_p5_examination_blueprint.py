"""
P5 Examination Blueprint & Template Tests
Validates the official CBSE 2026-27 Board Examination Blueprint (80 Marks, 180 Minutes, 39 Questions across 5 Sections).
"""

import pytest
from src.storage.database import Database
from src.storage.examination_repository import ExaminationRepository
from src.services.examination_service import ExaminationService
from src.models.question import QuestionType


@pytest.fixture(scope="module")
def shared_db():
    return Database("data/curriculum.db")


@pytest.fixture(scope="module")
def exam_repo(shared_db):
    return ExaminationRepository(shared_db)


@pytest.fixture(scope="module")
def exam_svc(shared_db, exam_repo):
    from src.storage.question_repository import QuestionRepository
    from src.storage.concept_repository import ConceptRepository
    from src.storage.remediation_repository import RemediationRepository
    from src.storage.learner_repository import LearnerRepository
    from src.services.answer_evaluation_service import AnswerEvaluationService
    from src.services.learner_model_service import LearnerModelService
    from src.services.misconception_detection_service import MisconceptionDetectionService
    from src.services.spaced_repetition_service import SpacedRepetitionService

    q_repo = QuestionRepository(shared_db)
    c_repo = ConceptRepository(shared_db)
    r_repo = RemediationRepository(shared_db)
    l_repo = LearnerRepository(shared_db)
    
    return ExaminationService(
        db=shared_db,
        exam_repo=exam_repo,
        question_repo=q_repo,
        concept_repo=c_repo,
        evaluation_service=AnswerEvaluationService(),
        learner_service=LearnerModelService(l_repo, None, c_repo),
        misconception_service=MisconceptionDetectionService(r_repo, q_repo, c_repo),
        spaced_repetition_service=SpacedRepetitionService(r_repo, l_repo, c_repo),
    )


def test_official_cbse_blueprint_specifications(exam_repo):
    """Verifies that the flagship CBSE 2026-27 blueprint meets all official requirements."""
    bp = exam_repo.get_blueprint("BP-CBSE-X-SCI-2027")
    assert bp is not None, "Official blueprint BP-CBSE-X-SCI-2027 must be present."

    assert bp.total_marks == 80
    assert bp.duration_minutes == 180
    assert bp.question_count == 39
    assert bp.is_official is True
    assert bp.academic_session == "2026-27"


def test_sections_mark_and_question_sums(exam_repo):
    """Verifies that the 5 sections sum exactly to 39 questions and 80 marks."""
    bp = exam_repo.get_blueprint("BP-CBSE-X-SCI-2027")
    assert len(bp.sections) == 5, "CBSE Class 10 Science examination must consist of exactly 5 sections (A to E)."

    total_q = sum(s.question_count for s in bp.sections)
    total_m = sum(s.total_section_marks for s in bp.sections)

    assert total_q == 39, f"Expected 39 total questions, got {total_q}"
    assert total_m == 80, f"Expected 80 total marks, got {total_m}"

    sec_map = {s.section_name: s for s in bp.sections}
    # Section A: 20 Qs, 1m each = 20m
    assert sec_map["Section A"].question_count == 20
    assert sec_map["Section A"].marks_per_question == 1
    assert sec_map["Section A"].total_section_marks == 20
    assert QuestionType.MCQ in sec_map["Section A"].question_types
    assert QuestionType.ASSERTION_REASON in sec_map["Section A"].question_types

    # Section B: 6 Qs, 2m each = 12m
    assert sec_map["Section B"].question_count == 6
    assert sec_map["Section B"].marks_per_question == 2
    assert sec_map["Section B"].total_section_marks == 12

    # Section C: 7 Qs, 3m each = 21m
    assert sec_map["Section C"].question_count == 7
    assert sec_map["Section C"].marks_per_question == 3
    assert sec_map["Section C"].total_section_marks == 21

    # Section D: 3 Qs, 5m each = 15m
    assert sec_map["Section D"].question_count == 3
    assert sec_map["Section D"].marks_per_question == 5
    assert sec_map["Section D"].total_section_marks == 15

    # Section E: 3 Qs, 4m each = 12m
    assert sec_map["Section E"].question_count == 3
    assert sec_map["Section E"].marks_per_question == 4
    assert sec_map["Section E"].total_section_marks == 12
    assert QuestionType.CASE_BASED in sec_map["Section E"].question_types


def test_unit_weightage_distribution(exam_repo):
    """Verifies official CBSE 2026-27 syllabus unit weightage breakdown."""
    bp = exam_repo.get_blueprint("BP-CBSE-X-SCI-2027")
    weights = bp.unit_weightage

    assert sum(weights.values()) == 80, f"Unit weightages must sum to 80, got {sum(weights.values())}"
    assert any("Unit I" in k and v == 25 for k, v in weights.items())
    assert any("Unit II" in k and v == 25 for k, v in weights.items())
    assert any("Unit III" in k and v == 12 for k, v in weights.items())
    assert any("Unit IV" in k and v == 13 for k, v in weights.items())
    assert any("Unit V" in k and v == 5 for k, v in weights.items())


def test_template_generation_maps_39_questions(exam_svc):
    """Verifies that template generation produces exactly 39 questions for official exam."""
    tmpl_id = exam_svc.generate_or_get_template("BP-CBSE-X-SCI-2027")
    tmpl = exam_svc.exam_repo.get_template(tmpl_id)
    assert tmpl is not None

    import json
    qids = json.loads(tmpl["questions_sequence_json"])
    assert len(qids) == 39, f"Official template must sequence exactly 39 questions, got {len(qids)}"
    assert tmpl["total_marks"] == 80
