"""
Tests for Source Document Management and Traceability
"""

from src.services.source_service import SourceDocumentService
from src.models.classification import VerificationStatus


def test_register_source_documents(repo):
    src_service = SourceDocumentService(repo, sources_dir="sources")
    docs = src_service.register_available_sources()
    assert len(docs) >= 2

    cbse_doc = next(d for d in docs if d.document_id == "CBSE_SCI_10_2026_27")
    assert cbse_doc.subject_code == "086"
    assert cbse_doc.source_authority == "Central Board of Secondary Education (CBSE)"
    assert cbse_doc.page_count == 9
    assert cbse_doc.sha256_hash is not None
    assert len(cbse_doc.sha256_hash) == 64

    ncert_doc = next(d for d in docs if d.document_id == "NCERT_SCI_10_CH01")
    assert ncert_doc.page_count == 16
    assert ncert_doc.sha256_hash is not None


def test_source_audit_and_missing_sources(repo):
    src_service = SourceDocumentService(repo, sources_dir="sources")
    src_service.register_available_sources()
    audit = src_service.audit_sources()

    assert audit["primary_syllabus_verified"] is True
    assert audit["ncert_complete"] is False
    assert len(audit["missing_textbook_chapters"]) == 12  # Chapters 2 through 13
    assert audit["missing_textbook_chapters"][0]["chapter_number"] == 2
    assert audit["missing_textbook_chapters"][-1]["chapter_number"] == 13
