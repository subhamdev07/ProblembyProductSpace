"""
Unit Tests for Question Validation Service
Tests the deterministic 12-point quality validation engine across schema,
referential integrity, CBSE blueprint, answer key structure, provenance, and duplicate checks.
"""

import pytest
from src.services.question_validation_service import QuestionValidationService
from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.models.concept import ConceptVerificationStatus, SourceStatus


def test_validate_all_seeded_questions_pass(seeded_question_bank):
    """Verify that all 15 seeded Chapter 1 questions pass the 12-point validation suite."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)
    summary = validator.validate_all_questions()

    assert summary.total_evaluated == 15
    assert summary.valid_count == 15
    assert summary.invalid_count == 0
    assert summary.all_valid is True
    assert len(summary.errors_by_rule) == 0


def test_qv01_missing_or_short_fields(seeded_question_bank):
    """Test QV-01: Invalid ID prefix or overly brief question/explanation."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    # Invalid ID prefix
    q_bad_id = Question(
        question_id="BAD-ID-001",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res = validator.validate_question(q_bad_id)
    assert not res.is_valid
    assert any("QV-01" in err and "Must start with 'Q-'" in err for err in res.errors)


def test_qv02_qv03_mcq_structure_checks(seeded_question_bank):
    """Test QV-02 and QV-03: Options count and matching correct option."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    # MCQ with only 3 options (instead of 4)
    q_three_opts = Question(
        question_id="Q-TEST-3OPTS",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res = validator.validate_question(q_three_opts)
    assert not res.is_valid
    assert any("QV-02: MCQ must provide exactly 4 options" in err for err in res.errors)


def test_qv04_invalid_chapter_or_topic(seeded_question_bank):
    """Test QV-04: Non-existent chapter_id or topic_id."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    q_invalid_ch = Question(
        question_id="Q-TEST-INV-CH",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-99",  # Non-existent
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res = validator.validate_question(q_invalid_ch)
    assert not res.is_valid
    assert any("QV-04: chapter_id 'CH-99' does not exist" in err for err in res.errors)


def test_qv05_invalid_concept_reference(seeded_question_bank):
    """Test QV-05: Missing or non-existent concept ID."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    q_no_concepts = Question(
        question_id="Q-TEST-NO-CPT",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=[],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res = validator.validate_question(q_no_concepts)
    assert not res.is_valid
    assert any("QV-05: Question must be linked to at least 1 valid concept" in err for err in res.errors)

    q_fake_concept = Question(
        question_id="Q-TEST-FAKE-CPT",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH99-FAKE"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res2 = validator.validate_question(q_fake_concept)
    assert not res2.is_valid
    assert any("QV-05: Referenced concept_id 'CPT-CH99-FAKE' does not exist" in err for err in res2.errors)


def test_qv06_invalid_learning_outcome(seeded_question_bank):
    """Test QV-06: Non-existent learning outcome ID."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    q_fake_lo = Question(
        question_id="Q-TEST-FAKE-LO",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001"],
        learning_outcome_ids=["LO-NON-EXISTENT-99"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
    )
    res = validator.validate_question(q_fake_lo)
    assert not res.is_valid
    assert any("QV-06: Referenced learning outcome 'LO-NON-EXISTENT-99' does not exist" in err for err in res.errors)


def test_qv09_missing_provenance_on_validated(seeded_question_bank):
    """Test QV-09: A question marked VALIDATED must have a provenance record."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    q_no_prov = Question(
        question_id="Q-TEST-NO-PROV",
        question_text="A properly worded question with more than ten characters.",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001"],
        learning_outcome_ids=["LO-C1.3"],
        answer_key={"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_option": "A"},
        explanation="Valid long explanation text for testing purposes.",
        question_status=QuestionStatus.VALIDATED,
        provenance=None,
    )
    res = validator.validate_question(q_no_prov)
    assert not res.is_valid
    assert any("QV-09: VALIDATED question must have a non-null provenance record" in err for err in res.errors)


def test_qv10_duplicate_detection(seeded_question_bank):
    """Test QV-10: Exact duplicate question text detection."""
    repo = seeded_question_bank
    validator = QuestionValidationService(repo)

    existing = repo.get_all_questions()
    duplicate_q = Question(
        question_id="Q-CH01-DUP-001",
        question_text=existing[0].question_text,  # Identical text
        question_type=existing[0].question_type,
        chapter_id=existing[0].chapter_id,
        topic_id=existing[0].topic_id,
        concept_ids=existing[0].concept_ids,
        answer_key=existing[0].answer_key,
        explanation=existing[0].explanation,
        provenance=existing[0].provenance,
    )

    res = validator.validate_question(duplicate_q, existing_questions=existing)
    assert not res.is_valid
    assert any("QV-10: Exact duplicate question text detected" in err for err in res.errors)
