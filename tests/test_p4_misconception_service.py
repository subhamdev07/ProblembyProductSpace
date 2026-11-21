"""
Unit Tests for Evidence-Based Misconception Detection Engine (P4)
Verifies: SUSPECTED -> CONFIRMED -> RESOLVED transitions and evidence logging.
"""

import pytest
import sqlite3
from src.storage.database import Database
from src.storage.remediation_repository import RemediationRepository
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.models.remediation import MisconceptionStatus


@pytest.fixture
def p4_db(tmp_path):
    db_file = tmp_path / "test_p4_misc.db"
    db = Database(str(db_file))
    db.init_db()

    # Seed test student and chapter 1 concept
    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO academic_sessions (session_id, name, start_year, end_year) VALUES ('SESS-2026-27', '2026-27', 2026, 2027);")
        conn.execute("INSERT OR IGNORE INTO subjects (subject_id, code, name, class_level) VALUES ('SUBJ-SCI-10', '086', 'Science', 10);")
        conn.execute("INSERT OR IGNORE INTO curricula (curriculum_id, name, session_id, subject_id) VALUES ('CURR-CBSE-10', 'CBSE Class 10 Science', 'SESS-2026-27', 'SUBJ-SCI-10');")
        conn.execute("INSERT OR IGNORE INTO units (unit_id, unit_number, name, curriculum_id, verification_status) VALUES ('UNIT-01', 'I', 'Chemical Substances', 'CURR-CBSE-10', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO chapters (chapter_id, chapter_number, name, unit_id, curriculum_id, assessment_status, verification_status) VALUES ('CH-01', 1, 'Chemical Reactions', 'UNIT-01', 'CURR-CBSE-10', 'SUMMATIVE', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO topics (topic_id, chapter_id, name, assessment_status, verification_status) VALUES ('CH01-T01', 'CH-01', 'Chemical Equations', 'SUMMATIVE', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO concepts (concept_id, name, canonical_name, description, chapter_id, topic_id, concept_type, source_status, verification_status) VALUES ('CPT-CH01-020', 'Precipitation Reactions', 'precipitation_reactions', 'Insoluble salt formation', 'CH-01', 'CH01-T01', 'CORE', 'SOURCE_DERIVED', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES ('STU-MISC-01', 'Test Learner', 10);")
        conn.execute("""
            INSERT OR IGNORE INTO questions (
                question_id, question_text, question_type, chapter_id, topic_id,
                difficulty, cognitive_level, marks, expected_time_seconds, answer_key_json,
                explanation, misconception_tags_json, source_status, verification_status, question_status
            ) VALUES (
                'Q-TEST-001', 'Which is a precipitate?', 'MCQ', 'CH-01', 'CH01-T01',
                'EASY', 'KNOWLEDGE_UNDERSTANDING', 1, 60, '{"correct_option": "A", "options": {"A": "BaSO4", "B": "NaCl", "C": "H2O", "D": "CO2"}}',
                'BaSO4 is insoluble', '["CONFUSING_DISPLACEMENT_WITH_DOUBLE_DISPLACEMENT"]',
                'SOURCE_DERIVED', 'VERIFIED', 'VALIDATED'
            );
        """)
        conn.execute("INSERT OR IGNORE INTO question_concept_mappings (mapping_id, question_id, concept_id) VALUES ('M1', 'Q-TEST-001', 'CPT-CH01-020');")
    return db


def test_single_incorrect_mcq_does_not_confirm_misconception(p4_db):
    rem_repo = RemediationRepository(p4_db)
    q_repo = QuestionRepository(p4_db)
    c_repo = ConceptRepository(p4_db)
    service = MisconceptionDetectionService(rem_repo, q_repo, c_repo)

    # First incorrect attempt
    detected = service.analyze_student_answer(
        student_id="STU-MISC-01",
        question_id="Q-TEST-001",
        submitted_answer={"selected_option": "B"},
        is_correct=False
    )

    assert len(detected) >= 1
    item = detected[0]
    # Single incorrect answer MUST NOT automatically confirm misconception
    assert item.status == MisconceptionStatus.SUSPECTED
    assert item.evidence_count == 1
    assert "Submitted answer: '{'selected_option': 'B'}'" in item.evidence_text


def test_repeated_incorrect_mcq_promotes_to_confirmed(p4_db):
    rem_repo = RemediationRepository(p4_db)
    q_repo = QuestionRepository(p4_db)
    c_repo = ConceptRepository(p4_db)
    service = MisconceptionDetectionService(rem_repo, q_repo, c_repo)

    # First attempt -> SUSPECTED
    service.analyze_student_answer(
        student_id="STU-MISC-01",
        question_id="Q-TEST-001",
        submitted_answer={"selected_option": "B"},
        is_correct=False
    )

    # Second corroborated attempt -> CONFIRMED
    detected_2 = service.analyze_student_answer(
        student_id="STU-MISC-01",
        question_id="Q-TEST-001",
        submitted_answer={"selected_option": "C"},
        is_correct=False
    )

    assert len(detected_2) >= 1
    item_2 = detected_2[0]
    assert item_2.status == MisconceptionStatus.CONFIRMED
    assert item_2.evidence_count == 2


def test_correct_answer_resolves_misconception(p4_db):
    rem_repo = RemediationRepository(p4_db)
    q_repo = QuestionRepository(p4_db)
    c_repo = ConceptRepository(p4_db)
    service = MisconceptionDetectionService(rem_repo, q_repo, c_repo)

    # 1. Fail twice to confirm
    service.analyze_student_answer("STU-MISC-01", "Q-TEST-001", {"selected_option": "B"}, is_correct=False)
    service.analyze_student_answer("STU-MISC-01", "Q-TEST-001", {"selected_option": "C"}, is_correct=False)

    active_items = service.get_student_misconceptions("STU-MISC-01")
    assert any(m.status == MisconceptionStatus.CONFIRMED for m in active_items)

    # 2. Answer correctly on concept -> RESOLVED
    service.analyze_student_answer("STU-MISC-01", "Q-TEST-001", {"selected_option": "A"}, is_correct=True)

    all_items = service.get_student_misconceptions("STU-MISC-01")
    for m in all_items:
        if m.concept_id == "CPT-CH01-020":
            assert m.status == MisconceptionStatus.RESOLVED
