"""
Unit Tests for Question Domain Models
Validates Question, QuestionProvenance, Enums, and Pydantic validators for answer keys.
"""

import pytest
from pydantic import ValidationError

from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.models.concept import ConceptVerificationStatus, SourceStatus


def test_question_enums():
    """Verify enum members and values."""
    assert QuestionType.MCQ == "MCQ"
    assert QuestionType.ASSERTION_REASON == "ASSERTION_REASON"
    assert QuestionType.SHORT_ANSWER == "SHORT_ANSWER"
    assert QuestionType.LONG_ANSWER == "LONG_ANSWER"
    assert QuestionType.NUMERICAL == "NUMERICAL"
    assert QuestionType.CASE_BASED == "CASE_BASED"
    assert QuestionType.DIAGRAM_BASED == "DIAGRAM_BASED"

    assert QuestionDifficulty.EASY == "EASY"
    assert QuestionDifficulty.MEDIUM == "MEDIUM"
    assert QuestionDifficulty.HARD == "HARD"

    assert CognitiveLevel.KNOWLEDGE_UNDERSTANDING == "KNOWLEDGE_UNDERSTANDING"
    assert CognitiveLevel.APPLICATION == "APPLICATION"
    assert CognitiveLevel.ANALYZE_EVALUATE_CREATE == "ANALYZE_EVALUATE_CREATE"

    assert QuestionStatus.DRAFT == "DRAFT"
    assert QuestionStatus.PENDING_REVIEW == "PENDING_REVIEW"
    assert QuestionStatus.VALIDATED == "VALIDATED"
    assert QuestionStatus.REJECTED == "REJECTED"


def test_question_provenance():
    """Verify QuestionProvenance model instantiation and attributes."""
    prov = QuestionProvenance(
        source_document_id="NCERT_SCI_10_CH01",
        source_filename="jesc101.pdf",
        page_number=2,
        section_heading="1.1 Chemical Equations",
        verbatim_source_context="Activity 1.1: Clean a magnesium ribbon...",
    )
    assert prov.source_document_id == "NCERT_SCI_10_CH01"
    assert prov.source_filename == "jesc101.pdf"
    assert prov.page_number == 2
    assert prov.section_heading == "1.1 Chemical Equations"
    assert "Activity 1.1" in prov.verbatim_source_context


def test_valid_mcq_model():
    """Verify valid MCQ model creation."""
    q = Question(
        question_id="Q-TEST-001",
        question_text="Which gas is evolved when zinc reacts with dilute sulfuric acid?",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["C-CH01-001"],
        learning_outcome_ids=["LO-CH01-01"],
        difficulty=QuestionDifficulty.EASY,
        cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
        marks=1,
        expected_time_seconds=45,
        answer_key={
            "options": {
                "A": "Hydrogen ($H_2$)",
                "B": "Oxygen ($O_2$)",
                "C": "Nitrogen ($N_2$)",
                "D": "Carbon dioxide ($CO_2$)",
            },
            "correct_option": "A",
        },
        explanation="Zinc reacts with dilute sulfuric acid to evolve hydrogen gas.",
    )
    assert q.question_id == "Q-TEST-001"
    assert q.answer_key["correct_option"] == "A"
    assert len(q.answer_key["options"]) == 4


def test_invalid_mcq_missing_options():
    """Verify MCQ fails if options dict is missing."""
    with pytest.raises(ValidationError) as exc:
        Question(
            question_id="Q-ERR-001",
            question_text="Sample text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            answer_key={"correct_option": "A"},
            explanation="Explanation",
        )
    assert "MCQ answer_key must contain 'options' dict" in str(exc.value)


def test_invalid_mcq_correct_option_not_in_options():
    """Verify MCQ fails if correct_option is not among choices."""
    with pytest.raises(ValidationError) as exc:
        Question(
            question_id="Q-ERR-002",
            question_text="Sample text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            answer_key={
                "options": {"A": "Option 1", "B": "Option 2"},
                "correct_option": "C",
            },
            explanation="Explanation",
        )
    assert "correct_option 'C' must be a key in options" in str(exc.value)


def test_invalid_mcq_insufficient_options():
    """Verify MCQ fails if fewer than 2 options provided."""
    with pytest.raises(ValidationError) as exc:
        Question(
            question_id="Q-ERR-003",
            question_text="Sample text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            answer_key={"options": {"A": "Option 1"}, "correct_option": "A"},
            explanation="Explanation",
        )
    assert "at least 2 choices" in str(exc.value)


def test_valid_assertion_reason_model():
    """Verify valid Assertion-Reason model creation."""
    q = Question(
        question_id="Q-TEST-AR",
        question_text="Assertion: Iron articles get rusted when exposed to moist air.\nReason: Rusting is an oxidation process.",
        question_type=QuestionType.ASSERTION_REASON,
        chapter_id="CH-01",
        topic_id="CH01-T03",
        marks=1,
        expected_time_seconds=60,
        answer_key={
            "assertion": "Iron articles get rusted when exposed to moist air.",
            "reason": "Rusting is an oxidation process.",
            "correct_option": "A",
        },
        explanation="Both assertion and reason are true and reason is the correct explanation.",
    )
    assert q.question_type == QuestionType.ASSERTION_REASON
    assert q.answer_key["correct_option"] == "A"


def test_invalid_assertion_reason_option():
    """Verify Assertion-Reason fails if correct_option is not A/B/C/D."""
    with pytest.raises(ValidationError) as exc:
        Question(
            question_id="Q-ERR-AR",
            question_text="Sample text",
            question_type=QuestionType.ASSERTION_REASON,
            chapter_id="CH-01",
            topic_id="CH01-T03",
            answer_key={
                "assertion": "Assertion text",
                "reason": "Reason text",
                "correct_option": "E",
            },
            explanation="Explanation",
        )
    assert "must be one of {'A', 'B', 'C', 'D'}" in str(exc.value) or "Assertion-Reason correct_option must be one of" in str(exc.value)


def test_valid_numerical_model():
    """Verify valid Numerical model creation."""
    q = Question(
        question_id="Q-TEST-NUM",
        question_text="Calculate the mass of $CO_2$ produced by complete combustion of 12 g of carbon.",
        question_type=QuestionType.NUMERICAL,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        marks=2,
        expected_time_seconds=120,
        answer_key={
            "numerical_value": 44.0,
            "unit": "g",
            "tolerance": 0.5,
            "steps": ["C + O2 -> CO2", "12 g C yields 44 g CO2"],
        },
        explanation="1 mole of carbon (12 g) reacts with 1 mole of O2 (32 g) to form 44 g of CO2.",
    )
    assert q.answer_key["numerical_value"] == 44.0


def test_invalid_numerical_missing_value():
    """Verify Numerical fails if numerical_value is missing."""
    with pytest.raises(ValidationError) as exc:
        Question(
            question_id="Q-ERR-NUM",
            question_text="Calculate mass",
            question_type=QuestionType.NUMERICAL,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            answer_key={"unit": "g"},
            explanation="Explanation",
        )
    assert "NUMERICAL answer_key must contain 'numerical_value'" in str(exc.value)


def test_valid_short_answer_model():
    """Verify valid Short Answer model creation."""
    q = Question(
        question_id="Q-TEST-SA",
        question_text="Why do we apply paint on iron articles?",
        question_type=QuestionType.SHORT_ANSWER,
        chapter_id="CH-01",
        topic_id="CH01-T03",
        marks=2,
        expected_time_seconds=90,
        answer_key={
            "key_points": [
                "Paint forms a protective barrier.",
                "Prevents direct contact of iron with moisture and oxygen.",
            ],
            "sample_answer": "Paint cuts off contact with air and moisture.",
        },
        explanation="Painting isolates iron from oxygen and water vapor.",
    )
    assert "key_points" in q.answer_key


def test_valid_case_based_model():
    """Verify valid Case-Based model creation."""
    q = Question(
        question_id="Q-TEST-CB",
        question_text="Read the passage and answer the questions below.",
        question_type=QuestionType.CASE_BASED,
        chapter_id="CH-01",
        topic_id="CH01-T02",
        marks=4,
        expected_time_seconds=300,
        answer_key={
            "passage": "A student added dilute hydrochloric acid to copper oxide...",
            "sub_questions": [
                {"sub_id": "i", "question": "What is the color change?", "answer": "Blue-green"},
            ],
        },
        explanation="Copper(II) chloride forms which imparts a blue-green color.",
    )
    assert "passage" in q.answer_key
    assert len(q.answer_key["sub_questions"]) == 1


def test_question_constraints():
    """Verify marks and expected_time_seconds boundary validations."""
    with pytest.raises(ValidationError):
        # marks < 1
        Question(
            question_id="Q-ERR-M",
            question_text="Text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            marks=0,
            answer_key={"options": {"A": "1", "B": "2"}, "correct_option": "A"},
            explanation="Exp",
        )

    with pytest.raises(ValidationError):
        # marks > 10
        Question(
            question_id="Q-ERR-M2",
            question_text="Text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            marks=15,
            answer_key={"options": {"A": "1", "B": "2"}, "correct_option": "A"},
            explanation="Exp",
        )

    with pytest.raises(ValidationError):
        # time < 10
        Question(
            question_id="Q-ERR-T",
            question_text="Text",
            question_type=QuestionType.MCQ,
            chapter_id="CH-01",
            topic_id="CH01-T01",
            expected_time_seconds=5,
            answer_key={"options": {"A": "1", "B": "2"}, "correct_option": "A"},
            explanation="Exp",
        )
