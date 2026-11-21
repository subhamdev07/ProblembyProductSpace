"""
Unit Tests for Question Repository Layer
Tests SQLite persistence, transactional upsert, junction table integrity,
filtering, querying, and summary statistics.
"""

import pytest
from src.storage.question_repository import QuestionRepository
from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.models.concept import ConceptVerificationStatus, SourceStatus


@pytest.fixture
def sample_question():
    return Question(
        question_id="Q-TEST-REPO-001",
        question_text="Sample reaction question for testing?",
        question_type=QuestionType.MCQ,
        chapter_id="CH-01",
        topic_id="CH01-T01",
        concept_ids=["CPT-CH01-001", "CPT-CH01-002"],
        learning_outcome_ids=["LO-C1.3"],
        difficulty=QuestionDifficulty.EASY,
        cognitive_level=CognitiveLevel.KNOWLEDGE_UNDERSTANDING,
        marks=1,
        expected_time_seconds=60,
        answer_key={
            "options": {"A": "Option 1", "B": "Option 2"},
            "correct_option": "A",
        },
        explanation="Step by step solution.",
        misconception_tags=["MIS-01"],
        source_status=SourceStatus.SOURCE_DERIVED,
        verification_status=ConceptVerificationStatus.VERIFIED,
        question_status=QuestionStatus.VALIDATED,
        provenance=QuestionProvenance(
            source_document_id="NCERT_SCI_10_CH01",
            source_filename="jesc101.pdf",
            page_number=3,
            section_heading="1.1 Chemical Equations",
        ),
    )


def test_upsert_and_get_question(seeded_concept_repo, question_repo, sample_question):
    """Test inserting a question and retrieving it by question_id."""
    question_repo.upsert_question(sample_question)

    retrieved = question_repo.get_question("Q-TEST-REPO-001")
    assert retrieved is not None
    assert retrieved.question_id == "Q-TEST-REPO-001"
    assert retrieved.question_text == "Sample reaction question for testing?"
    assert retrieved.question_type == QuestionType.MCQ
    assert retrieved.difficulty == QuestionDifficulty.EASY
    assert retrieved.cognitive_level == CognitiveLevel.KNOWLEDGE_UNDERSTANDING
    assert retrieved.marks == 1
    assert retrieved.expected_time_seconds == 60
    assert retrieved.answer_key["correct_option"] == "A"
    assert "CPT-CH01-001" in retrieved.concept_ids
    assert "CPT-CH01-002" in retrieved.concept_ids
    assert "LO-C1.3" in retrieved.learning_outcome_ids
    assert retrieved.provenance is not None
    assert retrieved.provenance.page_number == 3


def test_upsert_updates_existing(seeded_concept_repo, question_repo, sample_question):
    """Test updating existing question in place without duplicating records."""
    question_repo.upsert_question(sample_question)

    sample_question.question_text = "Updated reaction question?"
    sample_question.difficulty = QuestionDifficulty.HARD
    sample_question.concept_ids = ["CPT-CH01-003"]
    question_repo.upsert_question(sample_question)

    updated = question_repo.get_question("Q-TEST-REPO-001")
    assert updated.question_text == "Updated reaction question?"
    assert updated.difficulty == QuestionDifficulty.HARD
    assert updated.concept_ids == ["CPT-CH01-003"]


def test_delete_question(seeded_concept_repo, question_repo, sample_question):
    """Test deleting a question and cascading junction records."""
    question_repo.upsert_question(sample_question)
    assert question_repo.get_question("Q-TEST-REPO-001") is not None

    deleted = question_repo.delete_question("Q-TEST-REPO-001")
    assert deleted is True
    assert question_repo.get_question("Q-TEST-REPO-001") is None

    # Deleting non-existent question returns False
    assert question_repo.delete_question("NON-EXISTENT") is False


def test_seeded_question_bank_queries(seeded_question_bank):
    """Test queries and filters against the 15 seeded Chapter 1 questions."""
    repo = seeded_question_bank

    # Total questions
    all_ch01 = repo.get_questions_by_chapter("CH-01")
    assert len(all_ch01) == 15

    # Filter by topic
    t01_qs = repo.get_questions_by_topic("CH01-T01")
    assert len(t01_qs) > 0

    # Filter by difficulty
    easy_qs = repo.filter_questions(chapter_id="CH-01", difficulty=QuestionDifficulty.EASY)
    med_qs = repo.filter_questions(chapter_id="CH-01", difficulty=QuestionDifficulty.MEDIUM)
    hard_qs = repo.filter_questions(chapter_id="CH-01", difficulty=QuestionDifficulty.HARD)
    assert len(easy_qs) == 5
    assert len(med_qs) == 5
    assert len(hard_qs) == 5

    # Filter by question_type
    mcqs = repo.filter_questions(question_type=QuestionType.MCQ)
    assert len(mcqs) == 5

    num_qs = repo.filter_questions(question_type=QuestionType.NUMERICAL)
    assert len(num_qs) == 2

    case_qs = repo.filter_questions(question_type=QuestionType.CASE_BASED)
    assert len(case_qs) == 1

    # Filter by concept
    c01_qs = repo.get_questions_by_concept("CPT-CH01-001")
    assert len(c01_qs) >= 1


def test_question_statistics(seeded_question_bank):
    """Test aggregated statistical metrics generation."""
    repo = seeded_question_bank
    stats = repo.get_question_statistics()

    assert stats["total_questions"] == 15
    assert stats["by_difficulty"]["EASY"] == 5
    assert stats["by_difficulty"]["MEDIUM"] == 5
    assert stats["by_difficulty"]["HARD"] == 5
    assert stats["by_question_type"]["MCQ"] == 5
    assert stats["by_question_type"]["SHORT_ANSWER"] == 3
    assert stats["by_question_type"]["ASSERTION_REASON"] == 2
    assert stats["by_question_type"]["NUMERICAL"] == 2
    assert stats["by_question_type"]["CASE_BASED"] == 1
    assert stats["by_question_type"]["LONG_ANSWER"] == 1
    assert stats["by_question_type"]["DIAGRAM_BASED"] == 1
    assert stats["distinct_concepts_covered"] >= 20
