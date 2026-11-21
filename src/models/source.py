"""
Source Document Management and Traceability Models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.models.classification import VerificationStatus


class SourceReference(BaseModel):
    """
    Fine-grained citation link connecting a curriculum entity to a primary source document.
    """
    document_id: str = Field(..., description="Unique ID of the source document")
    page_start: Optional[int] = Field(None, description="Starting page in primary document")
    page_end: Optional[int] = Field(None, description="Ending page in primary document")
    section: Optional[str] = Field(None, description="Section heading or structural anchor")
    verbatim_quote: Optional[str] = Field(None, description="Exact textual excerpt from source")


class SourceDocument(BaseModel):
    """
    Registered primary source document in the curriculum repository.
    """
    document_id: str = Field(..., description="Unique immutable document identifier")
    title: str = Field(..., description="Official title of the document")
    document_type: str = Field(..., description="Type: SYLLABUS, TEXTBOOK, MANUAL, GUIDELINES")
    academic_session: str = Field(..., description="Academic session (e.g. 2026-27)")
    subject: str = Field(..., description="Subject name (e.g. Science)")
    subject_code: Optional[str] = Field(None, description="Official subject code (e.g. 086)")
    source_authority: str = Field(..., description="Issuing authority (e.g. CBSE, NCERT)")
    file_path: Optional[str] = Field(None, description="Relative path within workspace")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    sha256_hash: Optional[str] = Field(None, description="Cryptographic SHA-256 digest")
    page_count: Optional[int] = Field(None, description="Total page count")
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary authority metadata")
