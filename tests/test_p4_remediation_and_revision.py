"""
Unit & Integration Tests for Targeted Remediation & Spaced Repetition (P4)
"""

import pytest
from src.storage.database import Database
from src.storage.remediation_repository import RemediationRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.question_repository import QuestionRepository
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.services.targeted_remediation_service import TargetedRemediationService
from src.models.spaced_repetition import ReviewStatus


@pytest.fixture
def p4_services(tmp_path):
    db_file = tmp_path / "test_p4_rem_rev.db"
    db = Database(str(db_file))
    db.init_db()

    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO academic_sessions (session_id, name, start_year, end_year) VALUES ('SESS-2026-27', '2026-27', 2026, 2027);")
        conn.execute("INSERT OR IGNORE INTO subjects (subject_id, code, name, class_level) VALUES ('SUBJ-SCI-10', '086', 'Science', 10);")
        conn.execute("INSERT OR IGNORE INTO curricula (curriculum_id, name, session_id, subject_id) VALUES ('CURR-CBSE-10', 'CBSE Class 10 Science', 'SESS-2026-27', 'SUBJ-SCI-10');")
        conn.execute("INSERT OR IGNORE INTO units (unit_id, unit_number, name, curriculum_id, verification_status) VALUES ('UNIT-01', 'I', 'Chemical Substances', 'CURR-CBSE-10', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO chapters (chapter_id, chapter_number, name, unit_id, curriculum_id, assessment_status, verification_status) VALUES ('CH-01', 1, 'Chemical Reactions', 'UNIT-01', 'CURR-CBSE-10', 'SUMMATIVE', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO topics (topic_id, chapter_id, name, assessment_status, verification_status) VALUES ('CH01-T01', 'CH-01', 'Chemical Equations', 'SUMMATIVE', 'VERIFIED');")
        
        # Prerequisites: CPT-CH01-019 is PREREQUISITE_OF CPT-CH01-020
        conn.execute("INSERT OR IGNORE INTO concepts (concept_id, name, canonical_name, description, chapter_id, topic_id, concept_type, source_status, verification_status) VALUES ('CPT-CH01-019', 'Double Displacement Reactions', 'double_displacement', 'Mutual exchange of ions', 'CH-01', 'CH01-T01', 'CORE', 'SOURCE_DERIVED', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO concepts (concept_id, name, canonical_name, description, chapter_id, topic_id, concept_type, source_status, verification_status) VALUES ('CPT-CH01-020', 'Precipitation Reactions', 'precipitation', 'Insoluble solid formation', 'CH-01', 'CH01-T01', 'APPLIED', 'SOURCE_DERIVED', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO concept_relationships (edge_id, source_concept_id, target_concept_id, relationship_type, confidence, verification_status) VALUES ('E1', 'CPT-CH01-019', 'CPT-CH01-020', 'PREREQUISITE_OF', 1.0, 'VERIFIED');")

        conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES ('STU-REM-01', 'Remediation Learner', 10);")
        conn.execute("""
            INSERT OR IGNORE INTO questions (
                question_id, question_text, question_type, chapter_id, topic_id,
                difficulty, cognitive_level, marks, expected_time_seconds, answer_key_json,
                explanation, misconception_tags_json, source_status, verification_status, question_status
            ) VALUES (
                'Q-REM-001', 'What is formed when sodium sulphate reacts with barium chloride?', 'MCQ', 'CH-01', 'CH01-T01',
                'EASY', 'KNOWLEDGE_UNDERSTANDING', 1, 60, '{"correct_option": "A", "options": {"A": "BaSO4 precipitate", "B": "NaCl precipitate"}}',
                'BaSO4 is insoluble and precipitates.', '["PRECIPITATE_CONFUSION"]',
                'SOURCE_DERIVED', 'VERIFIED', 'VALIDATED'
            );
        """)
        conn.execute("INSERT OR IGNORE INTO question_concept_mappings (mapping_id, question_id, concept_id) VALUES ('M-REM', 'Q-REM-001', 'CPT-CH01-020');")

    rem_repo = RemediationRepository(db)
    lrn_repo = LearnerRepository(db)
    c_repo = ConceptRepository(db)
    q_repo = QuestionRepository(db)
    eval_svc = AnswerEvaluationService()
    misc_svc = MisconceptionDetectionService(rem_repo, q_repo, c_repo)
    rev_svc = SpacedRepetitionService(rem_repo, lrn_repo, c_repo)
    target_svc = TargetedRemediationService(rem_repo, lrn_repo, c_repo, q_repo, eval_svc, misc_svc, rev_svc)

    return {
        "rem_repo": rem_repo,
        "lrn_repo": lrn_repo,
        "rev_svc": rev_svc,
        "target_svc": target_svc
    }


def test_targeted_remediation_generation(p4_services):
    svc = p4_services["target_svc"]

    payload = svc.get_remediation_for_student(
        student_id="STU-REM-01",
        concept_id="CPT-CH01-020"
    )

    assert payload.concept_id == "CPT-CH01-020"
    assert payload.concept_name == "Precipitation Reactions"
    assert payload.prerequisite_concept_id == "CPT-CH01-019"
    assert payload.prerequisite_concept_name == "Double Displacement Reactions"
    assert "NCERT" in payload.ncert_reference
    assert len(payload.explanation) > 30
    assert payload.practice_question is not None


def test_complete_remediation_practice_and_mastery_gain(p4_services):
    svc = p4_services["target_svc"]
    rem_repo = p4_services["rem_repo"]

    # 1. Fetch remediation
    rem_pkg = svc.get_remediation_for_student("STU-REM-01", "CPT-CH01-020")

    # 2. Complete practice answer correctly
    res = svc.complete_remediation_practice(
        remediation_id=rem_pkg.remediation_id,
        student_id="STU-REM-01",
        question_id="Q-REM-001",
        student_answer={"selected_option": "A"}
    )

    assert res.is_correct is True
    assert res.mastery_after > res.mastery_before
    assert res.next_revision_date is not None


def test_spaced_repetition_ladder_progression(p4_services):
    rev_svc = p4_services["rev_svc"]

    # First schedule
    sched = rev_svc.schedule_concept_review("STU-REM-01", "CPT-CH01-020", initial_interval_days=1)
    assert sched.interval_days == 1

    # First successful review -> advances to 3 days
    res1 = rev_svc.complete_revision("STU-REM-01", "CPT-CH01-020", is_correct=True)
    assert res1.new_interval_days == 3

    # Second successful review -> advances to 7 days
    res2 = rev_svc.complete_revision("STU-REM-01", "CPT-CH01-020", is_correct=True)
    assert res2.new_interval_days == 7

    # Failure -> collapses back to 1 day
    res3 = rev_svc.complete_revision("STU-REM-01", "CPT-CH01-020", is_correct=False)
    assert res3.new_interval_days == 1
