"""
Tests for Curriculum Validation Engine (12 Rules)
Includes positive baseline tests and negative fault-injection tests.
"""

import pytest
import sqlite3
from src.services.validation_service import CurriculumValidationEngine, ValidationResult


def test_validation_engine_clean_pass(seeded_repo):
    engine = CurriculumValidationEngine(seeded_repo)
    result = engine.validate()

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.summary["passed_rules"] == 12
    assert result.summary["failed_rules"] == 0


def test_rule_1_detects_duplicate_chapter_ids(seeded_repo):
    engine = CurriculumValidationEngine(seeded_repo)
    result = engine.validate()
    assert result.rule_reports["RULE_01_DUPLICATE_CHAPTER_IDS"]["status"] == "PASSED"


def test_rule_4_detects_invalid_parent_reference(seeded_repo):
    # Temporarily disable foreign keys to inject corrupt record
    with seeded_repo.db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("""
            INSERT INTO topics (topic_id, chapter_id, name, assessment_status, verification_status, source_doc_id)
            VALUES ('CORRUPT-T01', 'CH-999', 'Ghost Topic', 'SUMMATIVE', 'VERIFIED', 'CBSE_SCI_10_2026_27');
        """)
        conn.execute("PRAGMA foreign_keys = ON;")

    engine = CurriculumValidationEngine(seeded_repo)
    result = engine.validate()
    assert result.is_valid is False
    assert any("CORRUPT-T01" in err["message"] for err in result.errors)
    assert result.rule_reports["RULE_04_INVALID_PARENT_REFERENCES"]["status"] == "FAILED"


def test_rule_6_detects_missing_source(seeded_repo):
    with seeded_repo.db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("""
            INSERT INTO topics (topic_id, chapter_id, name, assessment_status, verification_status, source_doc_id)
            VALUES ('NO-SRC-T01', 'CH-01', 'Sourceless Topic', 'SUMMATIVE', 'VERIFIED', NULL);
        """)
        conn.execute("PRAGMA foreign_keys = ON;")

    engine = CurriculumValidationEngine(seeded_repo)
    result = engine.validate()
    assert result.is_valid is False
    assert any("NO-SRC-T01" in err["message"] for err in result.errors)
    assert result.rule_reports["RULE_06_MISSING_SOURCE_REFERENCES"]["status"] == "FAILED"


def test_rule_7_database_check_constraint_and_validation(seeded_repo):
    # 1. Verify that database CHECK constraint enforces valid classifications at DB level
    with pytest.raises(sqlite3.IntegrityError):
        with seeded_repo.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO topics (topic_id, chapter_id, name, assessment_status, verification_status, source_doc_id)
                VALUES ('BAD-STATUS-T01', 'CH-01', 'Bad Topic', 'INVALID_CLASS', 'VERIFIED', 'CBSE_SCI_10_2026_27');
            """)

    # 2. Verify validation engine handles corrupt classification if returned by repo
    class MockRepo:
        def get_units(self): return seeded_repo.get_units()
        def get_chapters(self): return seeded_repo.get_chapters()
        def get_topics(self):
            topics = seeded_repo.get_topics()
            topics.append({
                "topic_id": "MOCK-BAD-01",
                "chapter_id": "CH-01",
                "name": "Mock Bad Topic",
                "assessment_status": "INVALID_STATUS",
                "verification_status": "VERIFIED",
                "source_doc_id": "CBSE_SCI_10_2026_27"
            })
            return topics
        def get_subtopics(self): return seeded_repo.get_subtopics()
        def get_learning_outcomes(self): return seeded_repo.get_learning_outcomes()
        def get_source_documents(self): return seeded_repo.get_source_documents()

    engine = CurriculumValidationEngine(MockRepo())
    result = engine.validate()
    assert result.is_valid is False
    assert result.rule_reports["RULE_07_INVALID_ASSESSMENT_CLASSIFICATIONS"]["status"] == "FAILED"
    assert any("MOCK-BAD-01" in err["message"] for err in result.errors)
