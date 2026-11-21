"""
Data Models for AI Services (LLM & OCR)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """Chat completion message."""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message text content")


class LLMResponse(BaseModel):
    """
    Standardized LLM response object.
    Strictly separates user-facing content from internal reasoning tokens.
    """
    content: str = Field(..., description="Final response content intended for users/students")
    reasoning_content: Optional[str] = Field(None, description="Internal reasoning tokens (NOT exposed to students)")
    model: str = Field(..., description="Model identifier used for generation")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage statistics")
    latency_ms: float = Field(default=0.0, description="End-to-end request latency in milliseconds")
    finish_reason: Optional[str] = Field(None, description="Generation finish reason (e.g. stop, length)")


class OCRPageResult(BaseModel):
    """Extraction output for an individual document page."""
    page_number: int = Field(..., description="1-based page number")
    text: str = Field(default="", description="Extracted textual content")
    extraction_method: str = Field(..., description="'NATIVE_TEXT' via PyMuPDF or 'BODHAN_OCR'")
    confidence: Optional[float] = Field(None, description="Confidence score if reported by OCR engine; None if unavailable")
    character_count: int = Field(default=0, description="Total characters extracted")
    is_scanned_or_fallback: bool = Field(default=False, description="True if page required OCR conversion")
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'FAILED', or 'FLAGGED_FOR_REVIEW'")
    error_message: Optional[str] = Field(None, description="Details if page extraction encountered an error")


class DocumentExtractionResult(BaseModel):
    """Comprehensive multi-page document extraction result."""
    document_id: str = Field(..., description="Unique source document ID")
    file_path: Optional[str] = Field(None, description="Source PDF path")
    total_pages: int = Field(default=0, description="Total pages in document")
    native_pages_count: int = Field(default=0, description="Pages processed via native digital text")
    ocr_pages_count: int = Field(default=0, description="Pages routed to Bodhan Indic-OCR")
    failed_pages_count: int = Field(default=0, description="Pages that failed extraction")
    pages: List[OCRPageResult] = Field(default_factory=list, description="Ordered list of page extraction outputs")
    full_text: str = Field(default="", description="Concatenated document text in reading order")
    processing_time_ms: float = Field(default=0.0, description="Total processing time in ms")
    status: str = Field(default="COMPLETED", description="'COMPLETED', 'PARTIAL_SUCCESS', or 'FAILED'")
