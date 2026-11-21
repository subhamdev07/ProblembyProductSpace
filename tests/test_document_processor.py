"""
Unit and Integration Tests for Document Ingestion Pipeline
Tests PyMuPDF native text extraction, Bodhan OCR fallback, mixed PDF routing,
partial failure handling, page ordering, and metadata preservation.
"""

import pytest
import os
import tempfile
import fitz
from unittest.mock import MagicMock

from src.core.config import BodhanOCRConfig
from src.ai.ocr_service import BodhanOCRService
from src.ai.document_processor import DocumentProcessor
from src.core.exceptions import DocumentProcessingError, OCRError


@pytest.fixture
def sample_pdf():
    """Creates a temporary 3-page PDF:
       - Page 1: Digital text (Photosynthesis, >100 chars)
       - Page 2: Empty/low text (<20 chars, simulates scanned diagram)
       - Page 3: Digital text (Chemical equations, >100 chars)
    """
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    doc = fitz.open()

    # Page 1: Digital text
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Photosynthesis is the process by which green plants transform light energy into chemical energy. 6CO2 + 6H2O -> C6H12O6 + 6O2 in the presence of sunlight and chlorophyll.", fontsize=11)

    # Page 2: Empty / low text (scanned image simulation)
    p2 = doc.new_page()
    p2.insert_text((50, 50), "Fig 1.1", fontsize=10)

    # Page 3: Digital text
    p3 = doc.new_page()
    p3.insert_text((50, 50), "Ohm's Law: The potential difference V across the ends of a given metallic wire in an electric circuit is directly proportional to the current flowing through it, provided temperature remains constant.", fontsize=11)

    doc.save(path)
    doc.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


def test_digital_pdf_routing(sample_pdf):
    """Page 1 and Page 3 should be processed via NATIVE_TEXT."""
    mock_ocr = MagicMock(spec=BodhanOCRService)
    mock_ocr.extract_from_image_bytes.return_value = {
        "text": "OCR Extracted Fig 1.1 Diagram Details",
        "confidence": None,
        "model": "indic-ocr",
        "status": "SUCCESS"
    }

    processor = DocumentProcessor(ocr_service=mock_ocr, min_text_threshold=30)
    result = processor.process_pdf(sample_pdf, document_id="TEST-DOC-01")

    assert result.total_pages == 3
    assert result.native_pages_count == 2  # Pages 1 & 3
    assert result.ocr_pages_count == 1     # Page 2
    assert result.failed_pages_count == 0
    assert result.status == "COMPLETED"

    # Verify Page 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].extraction_method == "NATIVE_TEXT"
    assert "Photosynthesis" in result.pages[0].text

    # Verify Page 2 (OCR routed)
    assert result.pages[1].page_number == 2
    assert result.pages[1].extraction_method == "BODHAN_OCR"
    assert "OCR Extracted" in result.pages[1].text
    assert mock_ocr.extract_from_image_bytes.call_count == 1

    # Verify Page 3
    assert result.pages[2].page_number == 3
    assert result.pages[2].extraction_method == "NATIVE_TEXT"
    assert "Ohm's Law" in result.pages[2].text

    # Verify reading order in full text
    assert result.full_text.find("Photosynthesis") < result.full_text.find("OCR Extracted")
    assert result.full_text.find("OCR Extracted") < result.full_text.find("Ohm's Law")


def test_partial_ocr_failure_does_not_abort_document(sample_pdf):
    """When OCR fails on page 2, pages 1 and 3 must remain valid."""
    mock_ocr = MagicMock(spec=BodhanOCRService)
    mock_ocr.extract_from_image_bytes.side_effect = OCRError("Bodhan OCR 500 error on page 2")

    processor = DocumentProcessor(ocr_service=mock_ocr, min_text_threshold=30)
    result = processor.process_pdf(sample_pdf, document_id="TEST-PARTIAL-FAIL")

    assert result.total_pages == 3
    assert result.native_pages_count == 2
    assert result.ocr_pages_count == 1
    assert result.failed_pages_count == 1
    assert result.status == "PARTIAL_SUCCESS"

    assert result.pages[0].status == "SUCCESS"
    assert result.pages[1].status == "FAILED"
    assert "Bodhan OCR 500 error" in result.pages[1].error_message
    assert result.pages[2].status == "SUCCESS"


def test_ocr_unconfigured_flagged_for_review(sample_pdf):
    """When Bodhan API key is not configured, scanned pages are flagged for review without crashing."""
    cfg = BodhanOCRConfig(api_key=None)
    ocr_service = BodhanOCRService(cfg)

    processor = DocumentProcessor(ocr_service=ocr_service, min_text_threshold=30)
    result = processor.process_pdf(sample_pdf, document_id="TEST-UNCONFIGURED")

    assert result.total_pages == 3
    assert result.pages[1].status == "FLAGGED_FOR_REVIEW"
    assert result.pages[1].extraction_method == "OCR_UNCONFIGURED_FALLBACK"
    assert result.pages[0].status == "SUCCESS"
    assert result.pages[2].status == "SUCCESS"


def test_nonexistent_pdf_raises_error():
    processor = DocumentProcessor()
    with pytest.raises(DocumentProcessingError):
        processor.process_pdf("nonexistent_file_path.pdf")
