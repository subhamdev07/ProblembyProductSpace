"""
Unit Tests for Teacher Dashboard & Cohort Analytics (P4)
"""

import pytest
from src.storage.database import Database
from src.storage.learner_repository import LearnerRepository
from src.storage.remediation_repository import RemediationRepository
from src.storage.concept_repository import ConceptRepository
from src.services.teacher_dashboard_service import TeacherDashboardService


@pytest.fixture
def teacher_env(tmp_path):
    db_file = tmp_path / "test_p4_teacher.db"
    db = Database(str(db_file))
    db.init_db()

    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO academic_sessions (session_id, name, start_year, end_year) VALUES ('SESS-2026-27', '2026-27', 2026, 2027);")
        conn.execute("INSERT OR IGNORE INTO subjects (subject_id, code, name, class_level) VALUES ('SUBJ-SCI-10', '086', 'Science', 10);")
        conn.execute("INSERT OR IGNORE INTO curricula (curriculum_id, name, session_id, subject_id) VALUES ('CURR-CBSE-10', 'CBSE Class 10 Science', 'SESS-2026-27', 'SUBJ-SCI-10');")
        conn.execute("INSERT OR IGNORE INTO units (unit_id, unit_number, name, curriculum_id, verification_status) VALUES ('UNIT-01', 'I', 'Chemical Substances', 'CURR-CBSE-10', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO chapters (chapter_id, chapter_number, name, unit_id, curriculum_id, assessment_status, verification_status) VALUES ('CH-01', 1, 'Chemical Reactions', 'UNIT-01', 'CURR-CBSE-10', 'SUMMATIVE', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO topics (topic_id, chapter_id, name, assessment_status, verification_status) VALUES ('CH01-T01', 'CH-01', 'Chemical Equations', 'SUMMATIVE', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO concepts (concept_id, name, canonical_name, description, chapter_id, topic_id, concept_type, source_status, verification_status) VALUES ('CPT-CH01-020', 'Precipitation Reactions', 'precipitation', 'Insoluble solid formation', 'CH-01', 'CH01-T01', 'CORE', 'SOURCE_DERIVED', 'VERIFIED');")

        # Insert 2 students
        conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES ('STU-T1', 'Aarav Sharma', 10);")
        conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES ('STU-T2', 'Priya Patel', 10);")

        # Assessments
        conn.execute("INSERT OR IGNORE INTO assessments (assessment_id, student_id, assessment_type, chapter_id, status, total_questions, total_marks, score) VALUES ('ASM-T1', 'STU-T1', 'DIAGNOSTIC', 'CH-01', 'EVALUATED', 5, 5, 4.0);")
        conn.execute("INSERT OR IGNORE INTO assessments (assessment_id, student_id, assessment_type, chapter_id, status, total_questions, total_marks, score) VALUES ('ASM-T2', 'STU-T2', 'DIAGNOSTIC', 'CH-01', 'EVALUATED', 5, 5, 2.0);")

        # Learner Concept Mastery
        conn.execute("INSERT OR IGNORE INTO learner_concept_mastery (mastery_id, student_id, concept_id, mastery_score, confidence_score, total_attempts) VALUES ('M-1', 'STU-T1', 'CPT-CH01-020', 0.85, 0.87, 3);")
        conn.execute("INSERT OR IGNORE INTO learner_concept_mastery (mastery_id, student_id, concept_id, mastery_score, confidence_score, total_attempts) VALUES ('M-2', 'STU-T2', 'CPT-CH01-020', 0.35, 0.50, 1);")

        # Misconception for STU-T2
        conn.execute("INSERT OR IGNORE INTO student_misconceptions (misconception_record_id, student_id, concept_id, misconception_tag, status, evidence_count, evidence_text) VALUES ('MISC-T1', 'STU-T2', 'CPT-CH01-020', 'CONFUSING_DISPLACEMENT', 'CONFIRMED', 2, 'Confused displacement with double displacement.');")

    lrn_repo = LearnerRepository(db)
    rem_repo = RemediationRepository(db)
    c_repo = ConceptRepository(db)
    teacher_svc = TeacherDashboardService(db, lrn_repo, rem_repo, c_repo)

    return teacher_svc


def test_teacher_dashboard_access_control(teacher_env):
    svc = teacher_env

    # Valid teacher role succeeds
    data = svc.get_dashboard_summary(role="teacher")
    assert data.total_students == 2

    # Unauthorized role raises PermissionError
    with pytest.raises(PermissionError):
        svc.get_dashboard_summary(role="student")


def test_cohort_analytics_and_interventions(teacher_env):
    svc = teacher_env
    data = svc.get_dashboard_summary(role="teacher")

    assert data.total_students == 2
    assert data.total_assessments_completed == 2
    assert data.average_accuracy_pct == 3.0  # avg of 4.0 and 2.0
    # Priya Patel has mastery 0.35 -> requires intervention
    assert len(data.students_requiring_intervention) >= 1
    assert data.students_requiring_intervention[0]["student_id"] == "STU-T2"


def test_student_drilldown(teacher_env):
    svc = teacher_env
    drill = svc.get_student_drilldown(student_id="STU-T2", role="teacher")

    assert drill.student.student_id == "STU-T2"
    assert len(drill.active_misconceptions) >= 1
    assert drill.active_misconceptions[0].misconception_tag == "CONFUSING_DISPLACEMENT"
    assert len(drill.intervention_notes) >= 1
