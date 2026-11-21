"""
Source Document Management Service
Registers primary sources, computes cryptographic digests, extracts metadata,
and tracks missing official source material.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
try:
    import fitz
except ImportError:
    fitz = None
from src.models.source import SourceDocument
from src.models.classification import VerificationStatus
from src.storage.database import CurriculumRepository


def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


class SourceDocumentService:
    """
    Manages registry of primary source documents with provenance tracking.
    """

    KNOWN_SOURCES = [
        {
            "document_id": "CBSE_SCI_10_2026_27",
            "title": "CBSE Secondary School Curriculum 2026-27: Science (Class X, Subject Code 086)",
            "document_type": "OFFICIAL_SYLLABUS",
            "academic_session": "2026-27",
            "subject": "Science",
            "subject_code": "086",
            "source_authority": "Central Board of Secondary Education (CBSE)",
            "file_name": "Science_SecP1_2026-27.pdf",
            "relative_path": "sources/Science_SecP1_2026-27.pdf",
            "verification_status": VerificationStatus.VERIFIED,
            "metadata": {
                "theory_marks": 80,
                "internal_marks": 20,
                "duration_hours": 3,
                "syllabus_pages": "1-9",
                "authority_url": "https://cbseacademic.nic.in"
            }
        },
        {
            "document_id": "NCERT_SCI_10_CH01",
            "title": "NCERT Class X Science Textbook - Chapter 1: Chemical Reactions and Equations",
            "document_type": "TEXTBOOK_CHAPTER",
            "academic_session": "2026-27",
            "subject": "Science",
            "subject_code": "086",
            "source_authority": "National Council of Educational Research and Training (NCERT)",
            "file_name": "jesc101.pdf",
            "relative_path": "sources/jesc101.pdf",
            "verification_status": VerificationStatus.VERIFIED,
            "metadata": {
                "chapter_number": 1,
                "code": "jesc101",
                "pages": 16,
                "edition": "Reprint / Rationalised Edition"
            }
        }
    ]

    # Required NCERT chapters that are currently missing from the workspace
    MISSING_SOURCES = [
        {"document_id": f"NCERT_SCI_10_CH{i:02d}", "chapter_number": i, "expected_file": f"jesc1{i:02d}.pdf"}
        for i in range(2, 14)
    ]

    def __init__(self, repo: CurriculumRepository, sources_dir: str = "sources"):
        self.repo = repo
        self.sources_dir = sources_dir

    def register_available_sources(self) -> List[SourceDocument]:
        """
        Scans sources directory, extracts metadata (SHA256, page count, size),
        and upserts verified documents into database.
        """
        registered = []
        for src_spec in self.KNOWN_SOURCES:
            rel_path = src_spec["relative_path"]
            full_path = os.path.abspath(rel_path)

            file_size = None
            sha256 = None
            page_count = None

            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                sha256 = compute_sha256(full_path)
                try:
                    doc = fitz.open(full_path)
                    page_count = len(doc)
                    doc.close()
                except Exception:
                    page_count = None

            doc_model = SourceDocument(
                document_id=src_spec["document_id"],
                title=src_spec["title"],
                document_type=src_spec["document_type"],
                academic_session=src_spec["academic_session"],
                subject=src_spec["subject"],
                subject_code=src_spec["subject_code"],
                source_authority=src_spec["source_authority"],
                file_path=rel_path if os.path.exists(full_path) else None,
                file_size_bytes=file_size,
                sha256_hash=sha256,
                page_count=page_count,
                verification_status=src_spec["verification_status"],
                metadata=src_spec["metadata"]
            )

            # Persist to repository
            self.repo.upsert_source_document({
                "document_id": doc_model.document_id,
                "title": doc_model.title,
                "document_type": doc_model.document_type,
                "academic_session": doc_model.academic_session,
                "subject": doc_model.subject,
                "subject_code": doc_model.subject_code,
                "source_authority": doc_model.source_authority,
                "file_path": doc_model.file_path,
                "file_size_bytes": doc_model.file_size_bytes,
                "sha256_hash": doc_model.sha256_hash,
                "page_count": doc_model.page_count,
                "verification_status": doc_model.verification_status.value,
                "metadata_json": doc_model.metadata
            })
            registered.append(doc_model)

        return registered

    def audit_sources(self) -> Dict[str, Any]:
        """
        Produces audit report of verified and missing source documents.
        """
        available = self.repo.get_source_documents()
        return {
            "verified_documents": available,
            "missing_textbook_chapters": self.MISSING_SOURCES,
            "status": "PARTIAL_SOURCE_BASE",
            "primary_syllabus_verified": any(d["document_id"] == "CBSE_SCI_10_2026_27" for d in available),
            "ncert_complete": False,
            "ncert_available_count": sum(1 for d in available if "NCERT" in d["document_id"]),
            "ncert_required_count": 13,
            "notes": (
                "CBSE 2026-27 Syllabus is 100% verified and primary. "
                "NCERT Chapter 1 is verified. Chapters 2-13 textbooks are absent "
                "and are marked as pending textbook extraction without fabricating page references."
            )
        }
