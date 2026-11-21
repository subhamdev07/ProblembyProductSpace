"""
Document Ingestion Pipeline
Inspects PDFs, extracts native selectable text via PyMuPDF, identifies scanned or
image-only pages, converts only those pages into images, routes them to Bodhan Indic-OCR,
and aggregates results with source provenance and page ordering.
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
try:
    import fitz
except ImportError:
    fitz = None

from src.core.config import config, BodhanOCRConfig
from src.core.exceptions import (
    DocumentProcessingError,
    OCRConfigurationError,
    OCRError,
)
from src.ai.models import OCRPageResult, DocumentExtractionResult
from src.ai.ocr_service import BodhanOCRService

logger = logging.getLogger("ai.document_processor")


class DocumentProcessor:
    """
    Orchestrates hybrid PDF text extraction (PyMuPDF native + Bodhan OCR fallback).
    """

    def __init__(
        self,
        ocr_service: Optional[BodhanOCRService] = None,
        min_text_threshold: Optional[int] = None,
        dpi: Optional[int] = None,
    ):
        self.ocr_service = ocr_service or BodhanOCRService()
        self.min_text_threshold = (
            min_text_threshold
            if min_text_threshold is not None
            else config.bodhan.min_text_threshold_chars
        )
        self.dpi = dpi if dpi is not None else config.bodhan.image_dpi

    def process_pdf(
        self,
        pdf_path: str,
        document_id: Optional[str] = None,
        force_ocr: bool = False,
    ) -> DocumentExtractionResult:
        """
        Processes a PDF file, intelligently routing pages between native text extraction
        and Bodhan Indic-OCR. Preserves strict page numbering and order.
        """
        if not os.path.exists(pdf_path):
            raise DocumentProcessingError(f"File not found: {pdf_path}")

        start_time = time.perf_counter()
        doc_id = document_id or os.path.basename(pdf_path)

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise DocumentProcessingError(f"Failed to open PDF '{pdf_path}': {e}") from e

        total_pages = len(doc)
        page_results: List[OCRPageResult] = []
        native_count = 0
        ocr_count = 0
        failed_count = 0

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            try:
                # 1. Inspect native selectable text
                native_text = "" if force_ocr else page.get_text().strip()

                if native_text and len(native_text) >= self.min_text_threshold:
                    # Native digital text is sufficient
                    native_count += 1
                    page_results.append(OCRPageResult(
                        page_number=page_num,
                        text=native_text,
                        extraction_method="NATIVE_TEXT",
                        confidence=1.0,
                        character_count=len(native_text),
                        is_scanned_or_fallback=False,
                        status="SUCCESS"
                    ))
                else:
                    # Page is scanned, image-heavy, or has insufficient selectable text
                    logger.info(f"Page {page_num} in '{doc_id}' triggered OCR routing (chars: {len(native_text)} < threshold {self.min_text_threshold})")
                    ocr_count += 1

                    # 2. Convert page to image
                    try:
                        pix = page.get_pixmap(dpi=self.dpi)
                        img_bytes = pix.tobytes("png")
                    except Exception as conv_err:
                        failed_count += 1
                        page_results.append(OCRPageResult(
                            page_number=page_num,
                            text=native_text or "",
                            extraction_method="IMAGE_CONVERSION_FAILED",
                            is_scanned_or_fallback=True,
                            status="FAILED",
                            error_message=f"Failed to render page to image: {conv_err}"
                        ))
                        continue

                    # 3. Call Bodhan OCR Service
                    try:
                        ocr_resp = self.ocr_service.extract_from_image_bytes(img_bytes, mime_type="image/png")
                        extracted = ocr_resp.get("text", "")
                        page_results.append(OCRPageResult(
                            page_number=page_num,
                            text=extracted,
                            extraction_method="BODHAN_OCR",
                            confidence=ocr_resp.get("confidence"),
                            character_count=len(extracted),
                            is_scanned_or_fallback=True,
                            status="SUCCESS" if extracted.strip() else "FLAGGED_FOR_REVIEW"
                        ))
                    except OCRConfigurationError as ce:
                        # OCR not configured; preserve any native text and flag
                        logger.warning(f"Bodhan OCR unconfigured for page {page_num}: {ce}")
                        page_results.append(OCRPageResult(
                            page_number=page_num,
                            text=native_text or "",
                            extraction_method="OCR_UNCONFIGURED_FALLBACK",
                            is_scanned_or_fallback=True,
                            status="FLAGGED_FOR_REVIEW",
                            error_message="Bodhan API key not configured; OCR skipped for this page."
                        ))
                    except (OCRError, Exception) as ocr_err:
                        failed_count += 1
                        logger.error(f"OCR failed for page {page_num}: {ocr_err}")
                        page_results.append(OCRPageResult(
                            page_number=page_num,
                            text=native_text or "",
                            extraction_method="BODHAN_OCR_ERROR",
                            is_scanned_or_fallback=True,
                            status="FAILED",
                            error_message=str(ocr_err)
                        ))

            except Exception as unk_err:
                failed_count += 1
                page_results.append(OCRPageResult(
                    page_number=page_num,
                    text="",
                    extraction_method="PROCESSING_ERROR",
                    is_scanned_or_fallback=True,
                    status="FAILED",
                    error_message=f"Unhandled error processing page: {unk_err}"
                ))

        doc.close()

        total_time_ms = (time.perf_counter() - start_time) * 1000

        # Build concatenated full text in reading order
        full_text_parts = [
            f"--- [Page {p.page_number} ({p.extraction_method})] ---\n{p.text}"
            for p in page_results
            if p.text
        ]
        full_text = "\n\n".join(full_text_parts)

        # Overall document status
        if failed_count == 0:
            doc_status = "COMPLETED"
        elif failed_count < total_pages:
            doc_status = "PARTIAL_SUCCESS"
        else:
            doc_status = "FAILED"

        return DocumentExtractionResult(
            document_id=doc_id,
            file_path=pdf_path,
            total_pages=total_pages,
            native_pages_count=native_count,
            ocr_pages_count=ocr_count,
            failed_pages_count=failed_count,
            pages=page_results,
            full_text=full_text,
            processing_time_ms=round(total_time_ms, 2),
            status=doc_status
        )
