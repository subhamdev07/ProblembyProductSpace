"""
Unit Tests for Pydantic Models
"""

import pytest
from pydantic import ValidationError
from src.models.classification import AssessmentClassification, VerificationStatus, ProvenanceType
from src.models.source import SourceDocument, SourceReference
from src.models.session import AcademicSession, Subject, Curriculum
from src.models.hierarchy import Unit, Chapter, Topic, Subtopic
from src.models.learning_outcome import LearningOutcome


def test_assessment_classification_enum():
    assert AssessmentClassification.SUMMATIVE == "SUMMATIVE"
    assert AssessmentClassification.FORMATIVE == "FORMATIVE"
    assert AssessmentClassification.NOT_IN_CURRENT_SCOPE == "NOT_IN_CURRENT_SCOPE"
    assert AssessmentClassification.PENDING_VERIFICATION == "PENDING_VERIFICATION"


def test_verification_status_enum():
    assert VerificationStatus.VERIFIED == "VERIFIED"
    assert VerificationStatus.PENDING_VERIFICATION == "PENDING_VERIFICATION"
    assert VerificationStatus.UNVERIFIED == "UNVERIFIED"


def test_source_document_validation():
    doc = SourceDocument(
        document_id="DOC-01",
        title="Test Document",
        document_type="SYLLABUS",
        academic_session="2026-27",
        subject="Science",
        source_authority="CBSE",
        verification_status=VerificationStatus.VERIFIED
    )
    assert doc.document_id == "DOC-01"
    assert doc.verification_status == VerificationStatus.VERIFIED


def test_chapter_model_validation():
    ch = Chapter(
        chapter_id="CH-01",
        chapter_number=1,
        name="Chemical Reactions and Equations",
        unit_id="UNIT-01",
        curriculum_id="CBSE-SCI-10-2026-27",
        assessment_status=AssessmentClassification.SUMMATIVE,
        verification_status=VerificationStatus.VERIFIED
    )
    assert ch.chapter_number == 1
    assert ch.assessment_status == AssessmentClassification.SUMMATIVE


def test_chapter_model_missing_field():
    with pytest.raises(ValidationError):
        Chapter(
            chapter_id="CH-01",
            # missing chapter_number and name
            unit_id="UNIT-01",
            curriculum_id="CBSE-SCI-10-2026-27"
        )
